from pydantic import BaseModel, ConfigDict, Field, model_validator, StrictBool
from typing import Generic, List, Optional, TypeVar, Any, Dict, Union
from uuid import UUID
from datetime import datetime

from .schemas.feedbacks import FeedbackOut

T = TypeVar("T")

class PageLinks(BaseModel):
    prev: Optional[str] = None
    next: Optional[str] = None


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    links: Optional[PageLinks] = Field(default=None, alias="_links")
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
    dag: Optional['DagOut'] = None

class NodeOut(BaseModel):
    id: UUID
    run_id: UUID
    key: Optional[str] = None
    title: str
    status: str
    role: Optional[str] = None
    checksum: Optional[str] = None
    deps: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    feedbacks: List[FeedbackOut] = Field(default_factory=list)

class DagEdge(BaseModel):
    source: UUID
    target: UUID

class DagOut(BaseModel):
    nodes: List[NodeOut]
    edges: List[DagEdge] = Field(default_factory=list)

RunOut.model_rebuild()

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
    request_id: Optional[str] = None


# ---------- Agents ---------------------------------------------------------


class AgentOut(BaseModel):
    id: UUID
    name: str
    role: str
    domain: str
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentCreate(BaseModel):
    name: str
    role: str
    domain: str
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    domain: Optional[str] = None
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AgentMatrixOut(BaseModel):
    id: UUID
    role: str
    domain: str
    models: Dict[str, Any]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --------- Agent Templates & Matrix (CRUD) ------------------------------


class AgentTemplateOut(BaseModel):
    id: UUID
    name: str
    role: str
    domain: str
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentTemplateCreate(BaseModel):
    name: str
    role: str
    domain: str
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    domain: Optional[str] = None
    prompt_system: Optional[str] = None
    prompt_user: Optional[str] = None
    default_model: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentMatrixCreate(BaseModel):
    role: str
    domain: str
    models: Dict[str, Any] = Field(default_factory=dict)


class AgentMatrixUpdate(BaseModel):
    role: Optional[str] = None
    domain: Optional[str] = None
    models: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

__all__ = [
    name
    for name, obj in globals().items()
    if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
]
