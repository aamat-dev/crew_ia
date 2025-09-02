from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    """Payload pour créer un feedback."""

    run_id: UUID = Field(..., examples=["11111111-1111-1111-1111-111111111111"])
    node_id: UUID = Field(..., examples=["22222222-2222-2222-2222-222222222222"])
    source: str = Field(
        ..., description="Origine du feedback (auto ou human)", examples=["auto", "human"]
    )
    reviewer: Optional[str] = Field(
        default=None, examples=["reviewer-general"], description="Identité du reviewer"
    )
    score: int = Field(
        ge=0, le=100, description="Score d'évaluation entre 0 et 100", examples=[75]
    )
    comment: str = Field(
        ..., description="Commentaire du reviewer", examples=["Sortie invalide"]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Méta-données additionnelles", examples=[{"foo": "bar"}]
    )


class FeedbackOut(FeedbackCreate):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
