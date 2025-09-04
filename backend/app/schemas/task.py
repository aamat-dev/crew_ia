from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.core.models import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=10_000)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("description")
    @classmethod
    def _strip_desc(cls, v: Optional[str]) -> Optional[str]:
        return (v.strip() or None) if v is not None else None


class TaskOut(TaskCreate):
    id: UUID
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
