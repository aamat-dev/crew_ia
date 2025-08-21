# api/fastapi_app/routes/tasks.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Header
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from uuid import UUID
import os

from ..deps import api_key_auth
from core.services.orchestrator_service import schedule_run

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(api_key_auth)],  # 🔒 vérifie la valeur de la clé
)

# ---------- Schemas ----------

class Options(BaseModel):
    resume: bool = False
    dry_run: bool = False
    override: List[str] = Field(default_factory=list)

class TaskSpec(BaseModel):
    model_config = ConfigDict(extra="allow")  # tolère "plan", etc.

class TaskRequest(BaseModel):
    title: str = Field(..., examples=["Rapport 80p"])
    task: Optional[TaskSpec] = None
    task_spec: Optional[TaskSpec] = None
    task_file: Optional[str] = None
    options: Options = Field(default_factory=Options)
    llm: Optional[Dict[str, Any]] = None
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
    Lance l'orchestrateur en arrière-plan, répond 202 + run_id.
    Convertit proprement les erreurs d'entrée (ex: task_file manquant) en 400.
    """
    # Source du plan prioritaire: task_spec > task ; sinon task_file
    task_spec: Optional[Dict[str, Any]] = None
    if body.task_spec is not None:
        task_spec = body.task_spec.model_dump(exclude_unset=True)
    elif body.task is not None:
        task_spec = body.task.model_dump(exclude_unset=True)

    # Validation rapide côté API si on passe par un fichier
    if task_spec is None and body.task_file:
        # 1) existence
        if not os.path.isfile(body.task_file):
            raise HTTPException(status_code=400, detail=f"task_file not found: {body.task_file}")
        # 2) format
        if not body.task_file.lower().endswith(".json"):
            raise HTTPException(status_code=400, detail="task_file must be a .json file")

    # Propagation du request_id
    req_id = x_request_id or body.request_id

    try:
        run_id: UUID = await schedule_run(
            task_spec=task_spec,
            options=body.options,      # ✅ resume/dry_run/override transmis
            app_state=request.app.state,
            title=body.title,
            task_file=body.task_file,  # le service relira le JSON
            request_id=req_id,
        )
    except (FileNotFoundError, ValueError) as e:
        # Sécurité ceinture+bretelles si le service relance ce type d'erreurs
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Erreur interne inattendue
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return TaskAcceptedResponse(run_id=str(run_id), location=f"/runs/{run_id}")
