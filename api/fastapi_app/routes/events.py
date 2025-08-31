from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import datetime

import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, strict_api_key_auth, cap_date_range
from ..schemas import Page, EventOut
from app.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import Event  # type: ignore

router = APIRouter(prefix="", tags=["events"], dependencies=[Depends(strict_api_key_auth)])
_deprecated_warned = False
log = logging.getLogger("api.events")

ORDERABLE = {"timestamp": Event.timestamp, "level": Event.level}

@router.get("/events", response_model=Page[EventOut])
@router.get("/runs/{run_id_path}/events", response_model=Page[EventOut])
async def list_events(
    request: Request,
    response: Response,
    run_id: UUID | None = Query(None),
    run_id_path: UUID | None = None,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(pagination_params),
    level: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Recherche plein texte (message ILIKE)"),
    ts_from: Optional[datetime] = Query(None),
    ts_to: Optional[datetime] = Query(None),
    request_id: Optional[str] = Query(None),
):
    global _deprecated_warned
    run_id = run_id or run_id_path
    if run_id_path and not _deprecated_warned:
        log.warning("/runs/{run_id}/events est déprécié; utilisez /events?run_id=…")
        _deprecated_warned = True
    if run_id is None:
        raise HTTPException(status_code=400, detail="run_id requis")
    cap_date_range(ts_from, ts_to)

    where = [Event.run_id == run_id]
    if level:
        where.append(Event.level == level)
    if q:
        where.append(Event.message.ilike(f"%{q}%"))
    if ts_from:
        where.append(Event.timestamp >= ts_from)
    if ts_to:
        where.append(Event.timestamp <= ts_to)
    if request_id:
        where.append(Event.request_id == request_id)

    base = select(Event).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(Event.id)).select_from(Event).where(and_(*where))
        )
    ).scalar_one()
    stmt = apply_order(
        base, pagination.order_by, pagination.order_dir, ORDERABLE, "-timestamp"
    ).limit(pagination.limit).offset(pagination.offset)

    rows = (await session.execute(stmt)).scalars().all()
    items = [
        EventOut(
            id=e.id,
            run_id=e.run_id,
            node_id=getattr(e, "node_id", None),
            level=e.level,
            message=e.message,
            timestamp=e.timestamp,
            request_id=getattr(e, "request_id", None),
        )
        for e in rows
    ]
    set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[EventOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
