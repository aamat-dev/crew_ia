from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Generic, List, Optional, TypeVar, Any, Dict, Union
from uuid import UUID
from datetime import datetime

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    model_config = ConfigDict(json_schema_extra={"examples": [{"items": [], "total": 0, "limit": 50, "offset": 0}]})

# ---------- LLM options (facultatif) ----------
class LLMRoleOptions(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None

class LLMOptions(BaseModel):
    supervisor: Optional[LLMRoleOptions] = None
    manager: Optional[LLMRoleOptions] = None
    executor: Optional[LLMRoleOptions] = None

# ---------- Task options ----------
class TaskOptions(BaseModel):
    resume: bool = False
    dry_run: bool = False
    override: List[str] = Field(default_factory=list)
    use_supervisor: bool = False  # si vous déclenchez la génération via superviseur
    llm: Optional[LLMOptions] = None

# ---------- Task request ----------
class TaskRequest(BaseModel):
    title: str
    # Une seule des 2 sources est requise :
    task_file: Optional[str] = None       # chemin JSON (ex: examples/task_rapport_80p.json)
    task: Optional[Dict[str, Any]] = None # plan inline (doit contenir "plan":[...])

    # Compat : certains clients existaient déjà avec "task_spec"
    task_spec: Optional[Dict[str, Any]] = None

    options: TaskOptions = Field(default_factory=TaskOptions)
    request_id: Optional[str] = None

    @model_validator(mode="after")
    def _normalize_spec(self):
        # Priorité : task > task_file > task_spec
        src_count = sum(bool(x) for x in [self.task, self.task_file, self.task_spec])
        if src_count == 0:
            raise ValueError("Provide one of: task | task_file | task_spec")
        if src_count > 1:
            raise ValueError("Provide only one of: task | task_file | task_spec")

        # Normalise sur task_spec
        if self.task is not None:
            self.task_spec = self.task
        return self

class TaskAcceptedResponse(BaseModel):
    run_id: UUID
    status: str = "accepted"
    location: str

# --------- Exemples d’autres schémas existants (inchangés) ---------
class RunListItemOut(BaseModel):
    id: UUID
    title: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class RunOut(BaseModel):
    id: UUID
    title: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None

class RunSummaryOut(BaseModel):
    id: UUID
    title: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
