from __future__ import annotations
import json
import os
import uuid
from uuid import UUID
from pathlib import Path
import datetime as dt
from datetime import datetime
from typing import Optional

import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, strict_api_key_auth, cap_date_range, settings
from ..schemas_base import Page, EventOut
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import Event, Run  # type: ignore

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
    db_request_id = next((e.request_id for e in items if e.request_id), None)
    run_request_id = None
    run_row = await session.get(Run, run_id)
    if run_row and run_row.meta:
        meta_dict = run_row.meta
        if isinstance(meta_dict, str):
            try:
                meta_dict = json.loads(meta_dict)
            except Exception:
                meta_dict = {}
        run_request_id = meta_dict.get("request_id")
    if db_request_id is None:
        db_request_id = run_request_id
    if db_request_id is None:
        # Lecture de secours depuis le fichier run.json
        try:
            runs_root = Path(os.getenv("ARTIFACTS_DIR", settings.artifacts_dir))
            meta_json = json.loads((runs_root / str(run_id) / "run.json").read_text())
            db_request_id = meta_json.get("meta", {}).get("request_id")
        except Exception:
            db_request_id = None
    if db_request_id:
        # Injecte le request_id manquant dans les événements NODE_COMPLETED
        for e in items:
            if e.level == "NODE_COMPLETED" and not e.request_id:
                try:
                    meta_e = json.loads(e.message)
                except Exception:
                    continue
                if "request_id" not in meta_e:
                    meta_e["request_id"] = db_request_id
                    e.message = json.dumps(meta_e)
                e.request_id = db_request_id
    # Fallback: si aucun NODE_COMPLETED en base, on reconstruit depuis les artifacts *.llm.json
    if run_id and not any(e.level == "NODE_COMPLETED" for e in items):
        base = Path(os.getenv("ARTIFACTS_DIR", settings.artifacts_dir)) / str(run_id) / "nodes"
        new_items = []
        if base.exists():
            for llm_path in base.glob("*/artifact_*.llm.json"):
                try:
                    meta = json.loads(llm_path.read_text())
                except Exception:
                    continue
                usage = meta.get("usage") or {}
                usage.setdefault("completion_tokens", 0)
                meta["usage"] = usage
                req_id = db_request_id or run_request_id
                if req_id and "request_id" not in meta:
                    meta["request_id"] = req_id
                node_key = llm_path.parent.name
                try:
                    node_uuid = UUID(node_key)
                except Exception:
                    node_uuid = None
                new_items.append(
                    EventOut(
                        id=uuid.uuid4(),
                        run_id=run_id,
                        node_id=node_uuid,
                        level="NODE_COMPLETED",
                        message=json.dumps(meta),
                        timestamp=dt.datetime.utcnow(),
                        request_id=meta.get("request_id"),
                    )
                )
        if new_items:
            items.extend(new_items)
            items.sort(key=lambda e: e.timestamp, reverse=True)
            total = len(items)
    links = set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[EventOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )
