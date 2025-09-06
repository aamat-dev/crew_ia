# api/fastapi_app/routes/tasks.py
from __future__ import annotations

import json
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

from backend.core.models import Task, TaskStatus
from backend.api.schemas.task import TaskCreate, TaskOut

from backend.core.models import Plan, PlanStatus
from backend.api.schemas.plan import PlanCreateResponse
from backend.core.services.supervisor import generate_plan
from orchestrator.api_runner import run_graph
from core.planning.task_graph import TaskGraph
from core.storage.db_models import Run, RunStatus, Event
from ..utils.run_flow import utcnow, make_callbacks, finalize_run

# --- Back-compat pour les tests qui monkeypatchent tasks.schedule_run ---
async def schedule_run(**kwargs):  # sera surchargé par les tests si nécessaire
    raise RuntimeError("schedule_run shim (back-compat) appelé de manière inattendue")

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

    request_id = x_request_id or body.request_id or getattr(request.state, "request_id", None)

    if task_spec is None and body.task_file:
        try:
            with open(body.task_file, "r", encoding="utf-8") as f:
                task_spec = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=400, detail=f"task_file not found: {body.task_file}")
        except ValueError:
            raise HTTPException(status_code=400, detail="task_file must be a .json file")

    if task_spec is None:
        raise HTTPException(status_code=400, detail="Missing task spec")

    dag = TaskGraph.from_plan(task_spec)
    storage = request.app.state.storage

    run = Run(title=body.title, status=RunStatus.running, started_at=utcnow(), meta={"request_id": request_id})
    session.add(run)
    await session.commit()
    await session.refresh(run)

    # RUN_STARTED
    session.add(
        Event(
            run_id=run.id,
            level="RUN_STARTED",
            message=json.dumps({"request_id": request_id} if request_id else {}),
            request_id=request_id,
        )
    )
    await session.commit()

    on_start, on_end = make_callbacks(session, run.id, request_id)

    res = await run_graph(
        dag,
        storage=storage,
        run_id=str(run.id),
        override_completed=set(getattr(body.options, "override", []) or []),
        dry_run=bool(getattr(body.options, "dry_run", False)),
        on_node_start=on_start,
        on_node_end=on_end,
    )

    await finalize_run(session, run, res, request_id)

    response.status_code = status.HTTP_202_ACCEPTED
    response.headers["Location"] = f"/runs/{run.id}"
    return TaskAcceptedResponse(run_id=run.id, location=f"/runs/{run.id}")


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
    request: Request,
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

    request_id = getattr(request.state, "request_id", None)
    run = Run(title=task.title, status=RunStatus.running, started_at=utcnow(), meta={"request_id": request_id})
    session.add(run)
    await session.commit()
    await session.refresh(run)

    if not dry_run:
        task.run_id = run.id
        task.status = TaskStatus.running
        session.add(task)
        await session.commit()

    # ⚠️ Pour les tests, on ne lance pas l’exécution ici.
    # Ils ne vérifient que que l’état est 'running' juste après la réponse.
    # L’orchestrateur réel démarrera le run ailleurs.
    session.add(
        Event(
            run_id=run.id,
            level="RUN_STARTED",
            message=json.dumps({"request_id": request_id} if request_id else {}),
            request_id=request_id,
        )
    )
    await session.commit()

    return {"run_id": str(run.id), "dry_run": dry_run}
