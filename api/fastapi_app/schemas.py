from __future__ import annotations
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int

# --- Runs ---
class RunListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class RunSummaryOut(BaseModel):
    nodes_total: int
    nodes_completed: int
    nodes_failed: int
    artifacts_total: int
    events_total: int
    duration_ms: Optional[int] = None

class RunOut(RunListItemOut):
    summary: RunSummaryOut

# --- Nodes --- (adapté à votre schéma: created_at / updated_at)
class NodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    key: Optional[str] = None
    title: Optional[str] = None
    status: str
    checksum: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- Artifacts --- (avec champs content/summary et preview optionnel)
class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    node_id: UUID
    type: str
    path: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    preview: Optional[str] = None

# --- Events ---
class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: Optional[UUID] = None
    node_id: Optional[UUID] = None
    level: str
    message: str
    timestamp: datetime