from __future__ import annotations

import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Any

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, func, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlmodel import SQLModel, Field


class PlanStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    invalid = "invalid"


class Plan(SQLModel, table=True):
    __tablename__ = "plans"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    task_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    status: PlanStatus = Field(
        sa_column=Column(SAEnum(PlanStatus, name="planstatus"), nullable=False)
    )
    graph: Dict[str, Any] = Field(
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            nullable=False,
        )
    )
    version: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, server_default="1"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    __table_args__ = (Index("ix_plans_task_id", "task_id"),)
