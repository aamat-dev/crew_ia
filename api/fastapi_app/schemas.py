from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, List, Optional, TypeVar, Any, Dict
from uuid import UUID
from datetime import datetime

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0
        }]
    })

class RunListItemOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3",
            "title": "Rapport 80p",
            "status": "running",
            "started_at": "2025-08-17T12:18:41.591278Z",
            "ended_at": None
        }]
    })

class RunSummaryOut(BaseModel):
    nodes_total: int
    nodes_completed: int
    nodes_failed: int
    artifacts_total: int
    events_total: int
    duration_ms: Optional[int] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "nodes_total": 10,
            "nodes_completed": 9,
            "nodes_failed": 1,
            "artifacts_total": 12,
            "events_total": 134,
            "duration_ms": 58234
        }]
    })

class RunOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    summary: RunSummaryOut

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3",
            "title": "Rapport 80p",
            "status": "running",
            "started_at": "2025-08-17T12:18:41.591278Z",
            "ended_at": None,
            "summary": {
                "nodes_total": 10,
                "nodes_completed": 9,
                "nodes_failed": 1,
                "artifacts_total": 12,
                "events_total": 134,
                "duration_ms": 58234
            }
        }]
    })

class NodeOut(BaseModel):
    id: UUID
    run_id: UUID
    key: Optional[str] = None
    title: Optional[str] = None
    status: str
    checksum: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "c0c8b56d-1d8e-43d3-b46c-11b4b7a8f23b",
            "run_id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3",
            "key": "n1",
            "title": "Collecte données",
            "status": "completed",
            "checksum": None,
            "created_at": "2025-08-17T12:18:41.591278Z",
            "updated_at": "2025-08-17T12:19:01.123456Z"
        }]
    })

class ArtifactOut(BaseModel):
    id: UUID
    node_id: UUID
    type: str
    path: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    preview: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "e8481f71-3dbe-4b18-8a5e-cc6c1e8a0e1c",
            "node_id": "c0c8b56d-1d8e-43d3-b46c-11b4b7a8f23b",
            "type": "markdown",
            "path": "/runs/9a5a/artifacts/a1.md",
            "content": "# Titre\nRésumé…",
            "summary": "md",
            "created_at": "2025-08-17T12:20:03.000000Z",
            "preview": "# Titre"
        }]
    })

class EventOut(BaseModel):
    id: UUID
    run_id: Optional[UUID] = None
    node_id: Optional[UUID] = None
    level: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "a9c5028c-2b07-4f64-bcfe-de7d9cb2c02d",
            "run_id": "9a5a0d83-90b6-4d2a-81d5-9a3d3f99a7f3",
            "node_id": "c0c8b56d-1d8e-43d3-b46c-11b4b7a8f23b",
            "level": "ERROR",
            "message": "boom",
            "timestamp": "2025-08-17T12:21:02.000000Z"
        }]
    })

class TaskCreateIn(BaseModel):
    title: Optional[str] = Field(None, description="Titre du run")
    params: Dict[str, Any] = Field(default_factory=dict, description="Paramètres métier")

class TaskCreatedOut(BaseModel):
    run_id: UUID
    status: str = "accepted"