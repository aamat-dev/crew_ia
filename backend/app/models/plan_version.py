from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, Dict, Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlmodel import SQLModel, Field


class PlanVersion(SQLModel, table=True):
    __tablename__ = "plan_versions"

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
    numero_version: int = Field(sa_column=Column(Integer, nullable=False))
    graph: Dict[str, Any] = Field(
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            nullable=False,
        ),
    )
    reason: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )

