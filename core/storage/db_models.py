from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from uuid import uuid4, UUID
from enum import StrEnum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, DateTime

class RunStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"

class NodeStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"

def _uuid() -> UUID:
    return uuid4()

class Run(SQLModel, table=True):
    __tablename__ = "runs"
    id: UUID = Field(default_factory=_uuid, primary_key=True, index=True)
    title: str = Field(index=True)
    status: RunStatus = Field(default=RunStatus.pending)
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    ended_at:   Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    # ⬇️ attribut Python renommé en 'meta', colonne SQL gardée en 'metadata'
    meta: Optional[dict] = Field(
        default=None,
        sa_column=Column("metadata", JSONB)   # nom de colonne explicite
    )
    
class Node(SQLModel, table=True):
    __tablename__ = "nodes" 
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    run_id: UUID = Field(foreign_key="runs.id", index=True)
    # 👇 NOUVEAU : clé logique du plan (ex: "n1")
    key: Optional[str] = Field(default=None, index=True)

    title: str = Field(index=True)
    status: NodeStatus = Field(default=NodeStatus.pending, index=True)
    deps: list[str] = Field(default_factory=list, sa_column=Column(JSONB))
    checksum: Optional[str] = Field(default=None, index=True)
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))

class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"
    id: UUID = Field(default_factory=_uuid, primary_key=True, index=True)
    node_id: UUID = Field(index=True, foreign_key="nodes.id")
    type: str = Field(index=True)   # "markdown" | "sidecar" | "json" ...
    path: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime(timezone=True), index=True))

class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: UUID = Field(default_factory=_uuid, primary_key=True, index=True)
    run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="runs.id")
    node_id: Optional[UUID] = Field(default=None, index=True, foreign_key="nodes.id")
    level: str = Field(index=True)  # INFO | WARN | ERROR | DEBUG
    message: str
    timestamp: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime(timezone=True), index=True))
    extra: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
