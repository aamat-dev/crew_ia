from __future__ import annotations
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.fastapi_app.deps import get_session
from api.fastapi_app.models.feedback import Feedback

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


class FeedbackCreate(BaseModel):
    run_id: UUID
    node_id: UUID
    source: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    score: Optional[int] = Field(None, ge=0, le=100)
    comment: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None

    @validator("source")
    def _source_norm(cls, v: str) -> str:  # noqa: D401
        return v.strip()

    @validator("reviewer")
    def _reviewer_norm(cls, v: str) -> str:  # noqa: D401
        return v.strip()


class FeedbackOut(BaseModel):
    id: UUID
    run_id: UUID
    node_id: UUID
    source: str
    reviewer: str
    score: Optional[int]
    comment: Optional[str]


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_session),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
):
    fb = Feedback(
        run_id=payload.run_id,
        node_id=payload.node_id,
        source=payload.source,
        reviewer=payload.reviewer,
        score=payload.score,
        comment=payload.comment,
        evaluation=payload.evaluation,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackOut(
        id=fb.id,
        run_id=fb.run_id,
        node_id=fb.node_id,
        source=fb.source,
        reviewer=fb.reviewer,
        score=fb.score,
        comment=fb.comment,
    )
