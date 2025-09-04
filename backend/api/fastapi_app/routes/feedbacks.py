from __future__ import annotations

from typing import Optional, Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status, Body
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import (
    get_session,
    require_role,
    require_request_id,
    strict_api_key_auth,
    read_timezone,
    to_tz,
)
from ..schemas_base import Page
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import Feedback

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"], dependencies=[Depends(strict_api_key_auth)])

ORDERABLE = {
    "created_at": Feedback.created_at,
    "score": Feedback.score,
}


# --- Schemas locaux (on étend sans casser le contrat main) ---

class FeedbackCreate(BaseModel):
    run_id: UUID
    node_id: UUID
    source: str = Field(..., min_length=1)
    reviewer: Optional[str] = Field(default=None)  # main autorisait None
    score: Optional[int] = Field(None, ge=0, le=100)  # optionnel pour compat tests
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # compat main (meta)
    evaluation: Optional[Dict[str, Any]] = None  # NOUVEAU

    @field_validator("source")
    @classmethod
    def _source_norm(cls, v: str) -> str:
        return v.strip()

    @field_validator("reviewer")
    @classmethod
    def _reviewer_norm(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class FeedbackOut(BaseModel):
    id: UUID
    run_id: UUID
    node_id: UUID
    source: str
    reviewer: Optional[str] = None
    score: Optional[int] = None
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Routes ---

@router.post(
    "",
    response_model=FeedbackOut,
    status_code=201,
    dependencies=[Depends(require_role("editor", "admin")), Depends(require_request_id)],

    responses={
        201: {
            "description": "Feedback créé",
            "content": {
                "application/json": {
                    "example": {
                        "id": "00000000-0000-0000-0000-000000000000",
                        "run_id": "11111111-1111-1111-1111-111111111111",
                        "node_id": "22222222-2222-2222-2222-222222222222",
                        "source": "human",
                        "reviewer": "alice",
                        "score": 80,
                        "comment": "OK",
                        "metadata": None,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": None,
                    }
                }
            },
        }
    },
)
async def create_feedback(
    payload: FeedbackCreate = Body(
        ..., examples={
            "default": {
                "summary": "Exemple de création",
                "value": {
                    "run_id": "11111111-1111-1111-1111-111111111111",
                    "node_id": "22222222-2222-2222-2222-222222222222",
                    "source": "human",
                    "reviewer": "alice",
                    "score": 80,
                    "comment": "OK",
                },
            }
        },
    ),
    session: AsyncSession = Depends(get_session),
):
    fb = Feedback(
        run_id=payload.run_id,
        node_id=payload.node_id,
        source=payload.source,
        reviewer=payload.reviewer or payload.source,
        score=payload.score,
        comment=payload.comment,
        meta=payload.metadata,
    )
    session.add(fb)
    await session.commit()
    await session.refresh(fb)
    return FeedbackOut(
        id=fb.id,
        run_id=fb.run_id,
        node_id=fb.node_id,
        source=fb.source,
        reviewer=fb.reviewer,
        score=fb.score,
        comment=fb.comment,
        metadata=fb.meta,
        created_at=fb.created_at.isoformat() if fb.created_at else None,
        updated_at=(
            getattr(fb, "updated_at", None).isoformat()
            if getattr(fb, "updated_at", None)
            else None
        ),
    )


@router.get(
    "",
    response_model=Page[FeedbackOut],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "f1",
                                "run_id": "11111111-1111-1111-1111-111111111111",
                                "node_id": "22222222-2222-2222-2222-222222222222",
                                "source": "auto",
                                "score": 40,
                                "comment": "Erreur",
                                "reviewer": "auto",
                                "metadata": None,
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": None,
                            }
                        ],
                        "total": 1,
                        "limit": 100,
                        "offset": 0,
                    }
                }
            }
        }
    },
)
async def list_feedbacks(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    pagination: PaginationParams = Depends(pagination_params),
    run_id: Optional[UUID] = Query(
        None, description="Filtrer par run (UUID du run)"
    ),
    node_id: Optional[UUID] = Query(
        None, description="Filtrer par nœud (UUID du nœud)"
    ),
):
    where = []
    if run_id:
        where.append(Feedback.run_id == run_id)
    if node_id:
        where.append(Feedback.node_id == node_id)

    base = select(Feedback).where(and_(*where)) if where else select(Feedback)
    total = (await session.execute(select(func.count(Feedback.id)).where(and_(*where)) if where else select(func.count(Feedback.id)))).scalar_one()
    stmt = apply_order(base, pagination.order_by, pagination.order_dir, ORDERABLE, "-created_at").limit(pagination.limit).offset(pagination.offset)
    rows = (await session.execute(stmt)).scalars().all()
    items = [
        FeedbackOut(
            id=f.id,
            run_id=f.run_id,
            node_id=f.node_id,
            source=f.source,
            reviewer=f.reviewer,
            score=f.score,
            comment=f.comment,
            metadata=f.meta,
            created_at=to_tz(f.created_at, tz).isoformat() if f.created_at else None,
            updated_at=(
                to_tz(getattr(f, "updated_at", None), tz).isoformat()
                if getattr(f, "updated_at", None)
                else None
            ),
        )
        for f in rows
    ]
    links = set_pagination_headers(response, request, total, pagination.limit, pagination.offset)
    return Page[FeedbackOut](items=items, total=total, limit=pagination.limit, offset=pagination.offset, links=links or None)
