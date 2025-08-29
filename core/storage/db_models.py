# core/storage/db_models.py
from __future__ import annotations

import uuid
from enum import Enum
from datetime import datetime, UTC
from typing import Optional, List, Dict

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Enum as SAEnum, Text, String, func, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# ---------------- Enums ----------------

class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class NodeStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ---------------- Tables ----------------

class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    title: str = Field(sa_column=Column(String, nullable=False))
    status: RunStatus = Field(sa_column=Column(SAEnum(RunStatus, name="runstatus"), nullable=False))
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    # ⚠️ ne pas utiliser l'attribut Python "metadata" (réservé).
    meta: Optional[Dict] = Field(
        default=None,
        sa_column=Column("metadata", JSON, nullable=True),
    )


class Node(SQLModel, table=True):
    __tablename__ = "nodes"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    run_id: uuid.UUID = Field(sa_column=Column(PGUUID(as_uuid=True), nullable=False, index=True))
    # "key" = identifiant logique du DAG (ex: "n1", "n2"...)
    key: Optional[str] = Field(default=None, sa_column=Column(String, index=True))
    title: str = Field(sa_column=Column(String, nullable=False))
    status: NodeStatus = Field(sa_column=Column(SAEnum(NodeStatus, name="nodestatus"), nullable=False))
    role: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    deps: Optional[List[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    checksum: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    node_id: uuid.UUID = Field(sa_column=Column(PGUUID(as_uuid=True), nullable=False, index=True))
    type: str = Field(sa_column=Column(String, nullable=False))
    path: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    summary: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    run_id: Optional[uuid.UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), nullable=True, index=True))
    node_id: Optional[uuid.UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), nullable=True, index=True))
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    level: str = Field(sa_column=Column(String, nullable=False))
    message: str = Field(sa_column=Column(Text, nullable=False))
    request_id: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
