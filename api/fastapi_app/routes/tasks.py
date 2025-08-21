# api/fastapi_app/routes/tasks.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Header
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from uuid import UUID

from ..deps import api_key_auth  # ✅ valide la valeur de l’API key
from core.services.orchestrator_service import schedule_run

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(api_key_auth)],  # 🔒 protège /tasks
)

# ---------- Schemas d’entrée/sortie ----------

class Options(BaseModel):
    resume: bool = False
    dry_run: bool = False
    override: List[str] = Field(default_factory=list)  # ex: ["n2"]

class TaskSpec(BaseModel):
    # schéma minimal ; on tolère des champs libres comme "plan"
    model_config = ConfigDict(extra="allow")

class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str = Field(..., examples=["Rapport 80p"])
    # l’appelant peut envoyer soit "task", soit "task_spec"
    task: Optional[TaskSpec] = None
    task_spec: Optional[TaskSpec] = None
    task_file: Optional[str] = None
    options: Options = Field(default_factory=Options)
    llm: Optional[Dict[str, Any]] = None  # transmis tel quel à l’orchestrateur si besoin
    request_id: Optional[str] = None

class TaskAcceptedResponse(BaseModel):
    status: str = "accepted"
    run_id: str
    location: str

# ---------- Route ----------

@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    body: TaskRequest,
    request: Request,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """
    POST /tasks
      -> 202 Accepted immédiat {run_id, location}
      L’exécution est planifiée dans le TaskGroup du lifespan (fire‑and‑forget).
    """

    # Source du plan: task_spec > task > task_file
    task_spec: Optional[Dict[str, Any]] = None
    if body.task_spec is not None:
        task_spec = body.task_spec.model_dump(exclude_unset=True)
    elif body.task is not None:
        task_spec = body.task.model_dump(exclude_unset=True)

    # request_id: header > body.request_id
    req_id = x_request_id or body.request_id

    # planifier via le service (gère: create Run(running) + start_soon(...))
    run_id: UUID = await schedule_run(
        task_spec=task_spec,
        options=body.options,          # ✅ passe bien resume/dry_run/override
        app_state=request.app.state,
        title=body.title,
        task_file=body.task_file,      # ✅ 400 si fichier manquant côté service
        request_id=req_id,
    )

    return TaskAcceptedResponse(
        run_id=str(run_id),
        location=f"/runs/{run_id}",
    )
