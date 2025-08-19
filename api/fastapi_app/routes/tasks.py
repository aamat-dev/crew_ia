from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from uuid import UUID
import anyio

from core.storage.db_models import RunStatus

from ..deps import api_key_auth
from ..schemas import TaskRequest, TaskAcceptedResponse
from core.services.orchestrator_service import schedule_run

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(api_key_auth)])


@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(request: Request, payload: TaskRequest) -> TaskAcceptedResponse:
    run_id = await schedule_run(
        payload.task_spec, payload.options, app_state=request.app.state, title=payload.title
    )
    location = f"/runs/{run_id}"
    data = TaskAcceptedResponse(run_id=run_id, location=location)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=data.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get("/{run_id}")
async def get_task(run_id: UUID, request: Request):
    storage = request.app.state.storage
    run = await storage.get_run(run_id)
    if not run:
        return {"status": "not_found"}

    # Dans certains environnements, l'exécution de la tâche peut prendre
    # un peu plus de temps. Pour réduire les conditions de course, on attend
    # brièvement si le run est encore en cours.
    if run.status == RunStatus.running:
        for _ in range(5):
            await anyio.sleep(0.1)
            refreshed = await storage.get_run(run_id)
            if refreshed and refreshed.status != RunStatus.running:
                run = refreshed
                break

    return {
        "run_id": str(run_id),
        "status": run.status,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
    }
