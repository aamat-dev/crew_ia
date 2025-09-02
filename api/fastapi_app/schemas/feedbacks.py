from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    """Payload pour créer un feedback."""

    run_id: UUID = Field(..., examples=["11111111-1111-1111-1111-111111111111"])
    node_id: UUID = Field(..., examples=["22222222-2222-2222-2222-222222222222"])
    source: str = Field(..., examples=["auto", "human"])
    reviewer: Optional[str] = Field(
        default=None, examples=["reviewer-general"], description="Identité du reviewer"
    )
    score: int = Field(ge=0, le=100, examples=[75])
    comment: str = Field(..., examples=["Sortie invalide"])
    metadata: Optional[Dict[str, Any]] = Field(default=None, examples=[{"foo": "bar"}])


class FeedbackOut(FeedbackCreate):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
