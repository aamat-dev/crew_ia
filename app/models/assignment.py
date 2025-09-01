from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Text, func, Index, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import SQLModel, Field


class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    plan_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    node_id: str = Field(sa_column=Column(Text, nullable=False))
    role: str = Field(sa_column=Column(Text, nullable=False))
    agent_id: str = Field(sa_column=Column(Text, nullable=False))
    llm_backend: str = Field(sa_column=Column(Text, nullable=False))
    llm_model: str = Field(sa_column=Column(Text, nullable=False))
    params: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
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

    __table_args__ = (
        sa.UniqueConstraint("plan_id", "node_id", name="uq_assignments_plan_node"),
        Index("ix_assignments_plan_id", "plan_id"),
    )
