from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Dict, Any
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Text, Boolean, Integer, Index, UniqueConstraint, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlmodel import SQLModel, Field


class AgentRole(str, Enum):
    orchestrator = "orchestrator"
    supervisor = "supervisor"
    manager = "manager"
    executor = "executor"
    reviewer = "reviewer"
    recruiter = "recruiter"
    monitor = "monitor"


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    name: str = Field(sa_column=Column(Text, nullable=False))
    role: str = Field(sa_column=Column(sa.Enum(AgentRole, name="agentrole"), nullable=False))
    domain: str = Field(sa_column=Column(Text, nullable=False))
    prompt_system: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    prompt_user: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    default_model: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    parent_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
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
        Index("ix_agents_role_domain", "role", "domain"),
        Index("ix_agents_active", "is_active"),
        UniqueConstraint("name", "role", "domain", name="uq_agents_name_role_domain"),
    )


class AgentTemplate(SQLModel, table=True):
    __tablename__ = "agent_templates"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    name: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    role: str = Field(sa_column=Column(Text, nullable=False))
    domain: str = Field(sa_column=Column(Text, nullable=False))
    prompt_system: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    prompt_user: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    default_model: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
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
        UniqueConstraint("name", name="uq_agent_templates_name"),
    )


class AgentModelsMatrix(SQLModel, table=True):
    __tablename__ = "agent_models_matrix"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    role: str = Field(sa_column=Column(sa.Enum(AgentRole, name="agentrole"), nullable=False))
    domain: str = Field(sa_column=Column(Text, nullable=False))
    models: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            sa.JSON().with_variant(JSONB, "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
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
        UniqueConstraint("role", "domain", name="uq_agent_models_matrix_role_domain"),
    )
