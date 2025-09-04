# api/fastapi_app/routes/tasks.py
from __future__ import annotations

import logging
import os
import time
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi import Header
from pydantic import ValidationError

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import strict_api_key_auth, get_session
from ..schemas_base import TaskRequest, TaskAcceptedResponse

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskOut

from app.models.plan import Plan, PlanStatus
from app.schemas.plan import PlanCreateResponse
from app.services.supervisor import generate_plan
from app.services import orchestrator_adapter

from core.services.orchestrator_service import schedule_run

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(strict_api_key_auth)],  # 🔒 vérifie la valeur de la clé
)

log = logging.getLogger("api.tasks")

# ---------- Rate limit config ----------
RATE_LIMIT = 3
WINDOW_SEC = 60


def _check_rate_limit(request: Request) -> None:
    store: Dict[str, tuple[int, float]] = request.app.state.rate_limits
    ip = request.client.host if request.client else "?"
    api_key = request.headers.get("X-API-Key", "")
    key = f"{ip}:{api_key}"
    now = time.time()
    count, start = store.get(key, (0, now))
    if now - start > WINDOW_SEC:
        store[key] = (1, now)
        return
    if count >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    store[key] = (count + 1, start)

# ---------- Routes ----------

@router.post(
    "",
    response_model=TaskOut | TaskAcceptedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: Dict[str, Any],
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
):
    """Crée une tâche brouillon ou lance l'orchestrateur suivant le corps de requête.

    Exemple cURL (création simple)::

        curl -X POST http://localhost:8000/tasks \
             -H 'X-API-Key: <API_KEY>' \
             -H 'X-Request-ID: <UUIDv4>' \
             -H 'Content-Type: application/json' \
             -d '{"title": "T1", "description": "desc"}'
    """

    rid = x_request_id or str(uuid4())
    response.headers["X-Request-ID"] = rid

    # Branche simple: création d'une tâche brouillon
    allowed_keys = {"title", "description"}
    if set(payload.keys()) <= allowed_keys:
        try:
            data = TaskCreate.model_validate(payload)
        except ValidationError as e:
            errs = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in e.errors()]
            raise HTTPException(status_code=422, detail=errs)

        title = data.title

        exists = await session.execute(
            select(func.count())
            .select_from(Task)
            .where(func.lower(Task.title) == title.lower())
        )
        if exists.scalar_one() > 0:
            raise HTTPException(status_code=409, detail="task exists")

        now = datetime.now(UTC)
        task = Task(
            title=title,
            description=data.description,
            status=TaskStatus.draft,
            created_at=now,
            updated_at=now,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        response.headers["Location"] = f"/tasks/{task.id}"
        return TaskOut.model_validate(task)

    # Sinon: route orchestrateur (legacy)
    _check_rate_limit(request)

    try:
        body = TaskRequest.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    # Source du plan prioritaire: task_spec > task ; sinon task_file
    task_spec: Optional[Dict[str, Any]] = None
    if body.task_spec is not None:
        task_spec = body.task_spec.model_dump(exclude_unset=True)
    elif body.task is not None:
        task_spec = body.task.model_dump(exclude_unset=True)

    # Validation rapide côté API si on passe par un fichier
    if task_spec is None and body.task_file:
        if not os.path.isfile(body.task_file):
            raise HTTPException(status_code=400, detail=f"task_file not found: {body.task_file}")
        if not body.task_file.lower().endswith(".json"):
            raise HTTPException(status_code=400, detail="task_file must be a .json file")

    request_id = x_request_id or body.request_id

    try:
        run_id: UUID = await schedule_run(
            task_spec=task_spec,
            options=body.options,
            app_state=request.app.state,
            title=body.title,
            task_file=body.task_file,
            request_id=request_id,
        )
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    response.status_code = status.HTTP_202_ACCEPTED
    response.headers["Location"] = f"/runs/{run_id}"
    return TaskAcceptedResponse(run_id=str(run_id), location=f"/runs/{run_id}")


@router.post("/{task_id}/plan", response_model=PlanCreateResponse, status_code=status.HTTP_201_CREATED)
async def generate_task_plan(
    task_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """Génère et persiste un plan pour une tâche donnée."""

    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await generate_plan(task)

    plan = None
    if task.plan_id:
        plan = await session.get(Plan, task.plan_id)
    if plan:
        plan.graph = result.graph.model_dump()
        plan.status = result.status
        plan.version += 1
    else:
        plan = Plan(task_id=task.id, status=result.status, graph=result.graph.model_dump())
        session.add(plan)
        await session.flush()
        if result.status != PlanStatus.invalid:
            task.plan_id = plan.id

    await session.commit()

    req_id = x_request_id or getattr(request.state, "request_id", None)
    log.info(
        "plan generated",
        extra={"request_id": req_id, "task_id": str(task.id), "plan_id": str(plan.id), "status": result.status.value},
    )

    return PlanCreateResponse(plan_id=plan.id, status=plan.status, graph=result.graph)


@router.post("/{task_id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_task_run(
    task_id: UUID,
    dry_run: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Démarre un run pour un ``task_id`` donné."""
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.plan_id is None:
        raise HTTPException(status_code=409, detail="Plan missing")

    plan = (
        await session.execute(select(Plan).where(Plan.id == task.plan_id))
    ).scalar_one_or_none()
    if plan is None or plan.status != PlanStatus.ready:
        raise HTTPException(status_code=409, detail="Plan not ready")

    run_id = await orchestrator_adapter.start(plan.id, dry_run)

    if not dry_run:
        task.run_id = run_id
        task.status = TaskStatus.running
        session.add(task)
        await session.commit()

    return {"run_id": str(run_id), "dry_run": dry_run}
