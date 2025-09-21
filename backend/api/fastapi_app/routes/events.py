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
    db_total = total
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
    fs_request_id = None
    run_row = await session.get(Run, run_id)
    if run_row and run_row.meta:
        meta_dict = run_row.meta
        if isinstance(meta_dict, str):
            try:
                meta_dict = json.loads(meta_dict)
            except Exception:
                meta_dict = {}
        if not isinstance(meta_dict, dict):
            meta_dict = {}
        run_request_id = meta_dict.get("request_id")
    try:
        runs_root = Path(os.getenv("ARTIFACTS_DIR", settings.artifacts_dir))
        meta_json = json.loads((runs_root / str(run_id) / "run.json").read_text())
        fs_request_id = meta_json.get("meta", {}).get("request_id")
    except Exception:
        fs_request_id = None
    chosen_request_id = db_request_id or run_request_id or fs_request_id
    synthetic_items: list[EventOut] = []

    if chosen_request_id:
        # Injecte le request_id manquant dans les événements NODE_COMPLETED
        for e in items:
            if e.level == "NODE_COMPLETED" and not e.request_id:
                try:
                    meta_e = json.loads(e.message) if e.message else {}
                except Exception:
                    meta_e = {}
                meta_e.setdefault("request_id", chosen_request_id)
                usage_meta = meta_e.get("usage")
                if isinstance(usage_meta, dict):
                    usage_meta.setdefault("completion_tokens", 0)
                e.message = json.dumps(meta_e)
                e.request_id = chosen_request_id
    # Normalise les métadonnées LLM pour garantir completion_tokens
    for e in items:
        if e.level != "NODE_COMPLETED" or not e.message:
            continue
        try:
            meta_e = json.loads(e.message)
        except Exception:
            continue
        usage_meta = meta_e.get("usage")
        if isinstance(usage_meta, dict) and "completion_tokens" not in usage_meta:
            usage_meta.setdefault("completion_tokens", 0)
            e.message = json.dumps(meta_e)
    # Si l'événement de fin de run est manquant, le synthétiser à partir de l'état du run
    # uniquement si aucun filtre restrictif n'est actif (level/q/ts_from/ts_to/request_id)
    if run_row and pagination.offset == 0 and not any([level, q, ts_from, ts_to, request_id]):
        want_level = None
        status_str = str(run_row.status) if getattr(run_row, "status", None) is not None else ""
        if status_str.endswith("completed"):
            want_level = "RUN_COMPLETED"
        elif status_str.endswith("failed"):
            want_level = "RUN_FAILED"
        if want_level and not any(e.level == want_level for e in items):
            # ID déterministe pour stabilité entre routes
            synth_id = uuid.uuid5(uuid.NAMESPACE_URL, f"synthetic:run:{run_id}:RUN_COMPLETED")
            synthetic_items.append(
                EventOut(
                    id=synth_id,
                    run_id=run_id,
                    node_id=None,
                    level=want_level,
                    message=json.dumps({"request_id": chosen_request_id} if chosen_request_id else {}),
                    timestamp=(run_row.ended_at or dt.datetime.now(dt.timezone.utc)),
                    request_id=chosen_request_id,
                )
            )
    # Si aucun RUN_COMPLETED n'est présent mais qu'on a des NODE_COMPLETED,
    # on ajoute un RUN_COMPLETED synthétique pour refléter l'état courant (sans filtres).
    if pagination.offset == 0 and not any([level, q, ts_from, ts_to, request_id]) and not any(e.level == "RUN_COMPLETED" for e in items + synthetic_items):
        last_node_completed = next((e for e in items if e.level == "NODE_COMPLETED"), None)
        if last_node_completed:
            synth_id = uuid.uuid5(uuid.NAMESPACE_URL, f"synthetic:run:{run_id}:RUN_COMPLETED")
            synthetic_items.append(
                EventOut(
                    id=synth_id,
                    run_id=run_id,
                    node_id=None,
                    level="RUN_COMPLETED",
                    message=json.dumps({"request_id": chosen_request_id} if chosen_request_id else {}),
                    timestamp=last_node_completed.timestamp,
                    request_id=chosen_request_id,
                )
            )

    # Fallback: si aucun NODE_COMPLETED en base, on reconstruit depuis les artifacts *.llm.json
    if pagination.offset == 0 and run_id and not any([level, q, ts_from, ts_to, request_id]) and not any(e.level == "NODE_COMPLETED" for e in items):
        base = Path(os.getenv("ARTIFACTS_DIR", settings.artifacts_dir)) / str(run_id) / "nodes"
        if base.exists():
            for llm_path in base.glob("*/artifact_*.llm.json"):
                try:
                    meta = json.loads(llm_path.read_text())
                except Exception:
                    continue
                usage = meta.get("usage") or {}
                usage.setdefault("completion_tokens", 0)
                meta["usage"] = usage
                if chosen_request_id and "request_id" not in meta:
                    meta["request_id"] = chosen_request_id
                node_key = llm_path.parent.name
                try:
                    node_uuid = UUID(node_key)
                except Exception:
                    node_uuid = None
                synthetic_items.append(
                    EventOut(
                        id=uuid.uuid4(),
                        run_id=run_id,
                        node_id=node_uuid,
                        level="NODE_COMPLETED",
                        message=json.dumps(meta),
                        timestamp=dt.datetime.now(dt.timezone.utc),
                        request_id=meta.get("request_id"),
                    )
                )
    # Applique un tri cohérent avec order_by/order_dir sur les éléments synthétiques ajoutés
    # Par défaut (None), l'API ordonne par -timestamp
    order_by = pagination.order_by
    order_dir = pagination.order_dir or ("desc" if (order_by is None) else None)
    if synthetic_items:
        items.extend(synthetic_items)
        total = db_total + len(synthetic_items)
    else:
        total = db_total

    if (order_by is None) or (order_by in {"timestamp", "-timestamp"}):
        reverse = True if (order_by is None or order_by == "-timestamp" or order_dir == "desc") else False
        items.sort(key=lambda e: e.timestamp, reverse=reverse)

    if pagination.limit and len(items) > pagination.limit:
        items = items[: pagination.limit]
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
