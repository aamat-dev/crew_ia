from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import List

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlmodel import SQLModel, Field


class PlanReview(SQLModel, table=True):
    __tablename__ = "plan_reviews"

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
    version: int = Field(sa_column=Column(Integer, nullable=False))
    validated: bool = Field(sa_column=Column(Boolean, nullable=False))
    errors: List[str] = Field(
        default_factory=list,
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            nullable=False,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
