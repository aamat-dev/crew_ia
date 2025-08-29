from pydantic import BaseModel, ConfigDict, Field, model_validator, StrictBool
from typing import Generic, List, Optional, TypeVar, Any, Dict, Union
from uuid import UUID
from datetime import datetime

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    model_config = ConfigDict(json_schema_extra={"examples": [{"items": [], "total": 0, "limit": 20, "offset": 0}]})

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
    """Options de déclenchement d'une tâche."""

    model_config = ConfigDict(extra="forbid")

    resume: StrictBool = False
    dry_run: StrictBool = False
    override: List[str] = Field(default_factory=list)
    use_supervisor: StrictBool = False  # si vous déclenchez la génération via superviseur
    llm: Optional[LLMOptions] = None


# ---------- Task spec ----------
class NodeSpec(BaseModel):
    id: str
    title: str
    deps: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow")


class TaskSpec(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    plan: Optional[List[NodeSpec]] = None

    model_config = ConfigDict(extra="allow")

# ---------- Task request ----------
class TaskRequest(BaseModel):
    title: str
    # Une seule des 2 sources est requise :
    task_file: Optional[str] = None  # chemin JSON (ex: examples/task_rapport_80p.json)
    task: Optional[TaskSpec] = None  # plan inline (doit contenir "plan":[...])

    # Compat : certains clients existaient déjà avec "task_spec"
    task_spec: Optional[TaskSpec] = None

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
class RunSummaryOut(BaseModel):
    nodes_total: int
    nodes_completed: int
    nodes_failed: int
    artifacts_total: int
    events_total: int
    duration_ms: Optional[int] = None

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
    summary: Optional[RunSummaryOut] = None

class NodeOut(BaseModel):
    id: UUID
    run_id: UUID
    key: Optional[str] = None
    title: str
    status: str
    checksum: Optional[str] = None
    deps: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ArtifactOut(BaseModel):
    id: UUID
    node_id: UUID
    type: str
    path: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    preview: Optional[str] = None

class EventOut(BaseModel):
    id: UUID
    run_id: UUID
    node_id: Optional[UUID] = None
    level: str
    message: str
    timestamp: datetime

__all__ = [
    name
    for name, obj in globals().items()
    if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
]
