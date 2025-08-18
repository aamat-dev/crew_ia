from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, require_api_key, read_timezone, to_tz
from ..schemas import Page, NodeOut
from core.storage.db_models import Node  # type: ignore

router = APIRouter(prefix="", tags=["nodes"], dependencies=[Depends(require_api_key)])

ORDERABLE = {
    "created_at": Node.created_at,
    "updated_at": Node.updated_at,
    "key": Node.key,
    "title": Node.title,
    "status": Node.status,
}

def order(stmt, order_by: str | None):
    if not order_by:
        return stmt.order_by(desc(Node.created_at))
    key = order_by.lstrip("-")
    direction = desc if order_by.startswith("-") else asc
    col = ORDERABLE.get(key, Node.created_at)
    return stmt.order_by(direction(col))

@router.get("/runs/{run_id}/nodes", response_model=Page[NodeOut])
async def list_nodes(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    title_contains: Optional[str] = Query(None),
    order_by: Optional[str] = Query("-created_at"),
):
    where = [Node.run_id == run_id]
    if status:
        where.append(Node.status == status)
    if key:
        where.append(Node.key == key)
    if title_contains:
        where.append(Node.title.ilike(f"%{title_contains}%"))

    base = select(Node).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(Node.id))
            .select_from(Node)
            .where(and_(*where))
        )
    ).scalar_one()
    stmt = order(base, order_by).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).scalars().all()
    items = [
        NodeOut(
            id=n.id,
            run_id=n.run_id,
            key=n.key,
            title=n.title,
            status=n.status,
            checksum=n.checksum,
            created_at=to_tz(n.created_at, tz),
            updated_at=to_tz(n.updated_at, tz),
        )
        for n in rows
    ]
    return Page[NodeOut](items=items, total=total, limit=limit, offset=offset)