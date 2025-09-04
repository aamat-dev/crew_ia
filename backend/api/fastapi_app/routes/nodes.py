from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import (
    get_session,
    read_timezone,
    to_tz,
    strict_api_key_auth,
)
from ..schemas_base import Page, NodeOut
from ..schemas.feedbacks import FeedbackOut
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import Node, Feedback  # type: ignore

router = APIRouter(prefix="/runs", tags=["nodes"], dependencies=[Depends(strict_api_key_auth)])

ORDERABLE = {
    "created_at": Node.created_at,
    "updated_at": Node.updated_at,
    "key": Node.key,
    "title": Node.title,
    "status": Node.status,
}

@router.get("/{run_id}/nodes", response_model=Page[NodeOut])
async def list_nodes(
    run_id: UUID,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    pagination: PaginationParams = Depends(pagination_params),
    status: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    title_contains: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    checksum: Optional[str] = Query(None),
):
    where = [Node.run_id == run_id]
    if status:
        where.append(Node.status == status)
    if key:
        where.append(Node.key == key)
    if title_contains:
        where.append(Node.title.ilike(f"%{title_contains}%"))
    if role:
        where.append(Node.role == role)
    if checksum:
        where.append(Node.checksum == checksum)

    base = select(Node).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(Node.id))
            .select_from(Node)
            .where(and_(*where))
        )
    ).scalar_one()
    stmt = apply_order(
        base, pagination.order_by, pagination.order_dir, ORDERABLE, "-created_at"
    ).limit(pagination.limit).offset(pagination.offset)

    rows = (await session.execute(stmt)).scalars().all()
    node_ids = [n.id for n in rows]
    fb_map = {nid: [] for nid in node_ids}
    if node_ids:
        fb_rows = (
            await session.execute(
                select(Feedback)
                .where(Feedback.node_id.in_(node_ids))
                .order_by(Feedback.created_at.desc())
            )
        ).scalars().all()
        for f in fb_rows:
            fb_map[f.node_id].append(
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
            )

    items = [
        NodeOut(
            id=n.id,
            run_id=n.run_id,
            key=n.key,
            title=n.title,
            status=n.status,
            role=n.role,
            checksum=n.checksum,
            created_at=to_tz(n.created_at, tz),
            updated_at=to_tz(n.updated_at, tz),
            feedbacks=fb_map.get(n.id, []),
        )
        for n in rows
    ]
    links = set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[NodeOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )
