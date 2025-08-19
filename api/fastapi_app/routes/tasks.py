from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse
from uuid import UUID
import os

from core.storage.db_models import RunStatus
from ..deps import api_key_auth
from ..schemas import TaskRequest, TaskAcceptedResponse
from core.services.orchestrator_service import schedule_run

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(api_key_auth)])

@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(req: TaskRequest, request: Request):
    """
    Lance l'orchestrateur sur un plan JSON (task_file) ou un plan inline (task).
    Répond 202 immédiatement avec le run_id et l’URL de suivi.
    """
    # Récupérer le X-Request-ID injecté par le middleware
    rid = getattr(getattr(request, "state", None), "request_id", None) or req.request_id

    # Normaliser la source du plan
    task_spec = req.task_spec
    task_file = req.task_file
    if task_file and not os.path.exists(task_file):
        raise HTTPException(status_code=400, detail=f"task_file not found: {task_file}")

    # Déléguer au service
    run_id: UUID = await schedule_run(
        task_spec=task_spec,
        options=req.options,
        app_state=request.app.state,
        title=req.title,
        task_file=task_file,
        request_id=rid,
    )

    return TaskAcceptedResponse(run_id=run_id, location=f"/runs/{run_id}")
