from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, require_api_key, read_timezone, to_tz
from ..schemas import Page, EventOut
from core.storage.db_models import Event  # type: ignore

from ..deps import api_key_auth

router = APIRouter(prefix="/runs", tags=["events"], dependencies=[Depends(api_key_auth)])

ORDERABLE = {"timestamp": Event.timestamp, "level": Event.level}

def order(stmt, order_by: str | None):
    if not order_by:
        return stmt.order_by(desc(Event.timestamp))
    key = order_by.lstrip("-")
    direction = desc if order_by.startswith("-") else asc
    col = ORDERABLE.get(key, Event.timestamp)
    return stmt.order_by(direction(col))

@router.get("/{run_id}/events", response_model=Page[EventOut])
async def list_events(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    level: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Recherche plein texte (message ILIKE)"),
    ts_from: Optional[datetime] = Query(None),
    ts_to: Optional[datetime] = Query(None),
    order_by: Optional[str] = Query("-timestamp"),
):
    where = [Event.run_id == run_id]
    if level:
        where.append(Event.level == level)
    if q:
        where.append(Event.message.ilike(f"%{q}%"))
    if ts_from:
        where.append(Event.timestamp >= ts_from)
    if ts_to:
        where.append(Event.timestamp <= ts_to)

    base = select(Event).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(Event.id))
            .select_from(Event)
            .where(and_(*where))
        )
    ).scalar_one()
    stmt = order(base, order_by).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).scalars().all()
    items = [
        EventOut(
            id=e.id,
            run_id=e.run_id,
            node_id=getattr(e, "node_id", None),
            level=e.level,
            message=e.message,
            timestamp=to_tz(e.timestamp, tz),
        )
        for e in rows
    ]
    return Page[EventOut](items=items, total=total, limit=limit, offset=offset)