from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime

import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, strict_api_key_auth, cap_limit, DEFAULT_LIMIT
from ..schemas import Page, EventOut
from ..pagination import set_pagination_headers
from core.storage.db_models import Event  # type: ignore

router = APIRouter(prefix="", tags=["events"], dependencies=[Depends(strict_api_key_auth)])
_deprecated_warned = False
log = logging.getLogger("api.events")

ORDERABLE = {"timestamp": Event.timestamp, "level": Event.level}

def order(stmt, order_by: str | None):
    if not order_by:
        return stmt.order_by(desc(Event.timestamp))
    key = order_by.lstrip("-")
    direction = desc if order_by.startswith("-") else asc
    col = ORDERABLE.get(key, Event.timestamp)
    return stmt.order_by(direction(col))

@router.get("/events", response_model=Page[EventOut])
@router.get("/runs/{run_id_path}/events", response_model=Page[EventOut])
async def list_events(
    request: Request,
    response: Response,
    run_id: UUID | None = Query(None),
    run_id_path: UUID | None = None,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    level: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Recherche plein texte (message ILIKE)"),
    ts_from: Optional[datetime] = Query(None),
    ts_to: Optional[datetime] = Query(None),
    order_by: Optional[str] = Query("-timestamp"),
):
    global _deprecated_warned
    limit = cap_limit(limit)
    run_id = run_id or run_id_path
    if run_id_path and not _deprecated_warned:
        log.warning("/runs/{run_id}/events est déprécié; utilisez /events?run_id=…")
        _deprecated_warned = True
    if run_id is None:
        raise HTTPException(status_code=400, detail="run_id requis")

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
            select(func.count(Event.id)).select_from(Event).where(and_(*where))
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
            timestamp=e.timestamp,
        )
        for e in rows
    ]
    set_pagination_headers(response, request, total, limit, offset)
    return Page[EventOut](items=items, total=total, limit=limit, offset=offset)
