# api/fastapi_app/routes/tasks.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Header
from pydantic import ValidationError
from typing import Optional, Any, Dict
from uuid import UUID
import os
import time

from ..deps import api_key_auth
from ..schemas import TaskRequest, TaskAcceptedResponse
from core.services.orchestrator_service import schedule_run

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(api_key_auth)],  # 🔒 vérifie la valeur de la clé
)

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

# ---------- Route ----------

@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    payload: Dict[str, Any],
    request: Request,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """Lance l'orchestrateur en arrière-plan, répond 202 + run_id."""

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

    return TaskAcceptedResponse(run_id=str(run_id), location=f"/runs/{run_id}")
