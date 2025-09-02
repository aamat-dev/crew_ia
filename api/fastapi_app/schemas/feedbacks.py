from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    run_id: UUID
    node_id: UUID
    source: str
    reviewer: Optional[str] = None
    score: int = Field(ge=0, le=100)
    comment: str
    metadata: Optional[Dict[str, Any]] = None


class FeedbackOut(FeedbackCreate):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
