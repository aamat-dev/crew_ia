from __future__ import annotations
from typing import Optional, Sequence, Literal
from uuid import UUID
from datetime import datetime
from sqlalchemy import join

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import (
    get_session,
    read_timezone,
    to_tz,
    strict_api_key_auth,
    cap_limit,
    cap_date_range,
    DEFAULT_LIMIT,
)
from ..schemas import Page, RunListItemOut, RunOut, RunSummaryOut
from ..pagination import set_pagination_headers
from ..ordering import apply_order

# Import des modèles ORM existants
from core.storage.db_models import Run, Node, Artifact, Event  # type: ignore

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(strict_api_key_auth)])

# Helpers
ORDERABLE_FIELDS = {
    "started_at": Run.started_at,
    "ended_at": Run.ended_at,
    "title": Run.title,
    "status": Run.status,
}

@router.get("", response_model=Page[RunListItemOut])
async def list_runs(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    limit: int = Query(DEFAULT_LIMIT, ge=1),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filtre par status"),
    title_contains: Optional[str] = Query(None, description="Filtre par sous-chaîne du titre"),
    started_from: Optional[datetime] = Query(None),
    started_to: Optional[datetime] = Query(None),
    order_by: Optional[str] = Query("-started_at"),
    order_dir: Optional[Literal["asc", "desc"]] = Query(None),
):
    limit = cap_limit(limit)
    cap_date_range(started_from, started_to)
    where_clauses = []
    if status:
        where_clauses.append(Run.status == status)
    if title_contains:
        like = f"%{title_contains}%"
        where_clauses.append(Run.title.ilike(like))
    if started_from:
        where_clauses.append(Run.started_at >= started_from)
    if started_to:
        where_clauses.append(Run.started_at <= started_to)

    base = select(Run)
    if where_clauses:
        base = base.where(and_(*where_clauses))

    total = (
        await session.execute(
            select(func.count(Run.id)).select_from(Run).where(and_(*where_clauses)) if where_clauses
            else select(func.count(Run.id)).select_from(Run)
        )
    ).scalar_one()

    stmt = apply_order(base, order_by, order_dir, ORDERABLE_FIELDS, "-started_at").limit(limit).offset(offset)
    runs = (await session.execute(stmt)).scalars().all()

    items = [
        RunListItemOut(
            id=r.id,
            title=r.title,
            status=r.status,
            started_at=to_tz(r.started_at, tz),
            ended_at=to_tz(getattr(r, "ended_at", None), tz),
        )
        for r in runs
    ]

    set_pagination_headers(response, request, total, limit, offset)
    return Page[RunListItemOut](items=items, total=total, limit=limit, offset=offset)

@router.get("/{run_id}", response_model=RunOut)
async def get_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    tz=Depends(read_timezone),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Counters
    nodes_q = select(func.count()).select_from(Node).where(Node.run_id == run_id)
    nodes_total = (await session.execute(nodes_q)).scalar_one()

    nodes_completed = (
        await session.execute(select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "completed"))
    ).scalar_one()
    nodes_failed = (
        await session.execute(select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "failed"))
    ).scalar_one()

    artifacts_total = (
        await session.execute(
            select(func.count(Artifact.id))
            .select_from(Artifact)
            .join(Node, Artifact.node_id == Node.id)
            .where(Node.run_id == run_id)
        )
    ).scalar_one()

    events_total = (
        await session.execute(select(func.count()).select_from(Event).where(Event.run_id == run_id))
    ).scalar_one()

    # Duration
    started = getattr(run, "started_at", None)
    ended = getattr(run, "ended_at", None)
    duration_ms = None
    if started and ended:
        duration_ms = int((ended - started).total_seconds() * 1000)

    return RunOut(
        id=run.id,
        title=run.title,
        status=run.status,
        started_at=to_tz(started, tz),
        ended_at=to_tz(ended, tz),
        summary=RunSummaryOut(
            nodes_total=nodes_total,
            nodes_completed=nodes_completed,
            nodes_failed=nodes_failed,
            artifacts_total=artifacts_total,
            events_total=events_total,
            duration_ms=duration_ms,
        ),
    )

@router.get("/{run_id}/summary", response_model=RunSummaryOut)
async def get_run_summary(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    nodes_total = (
        await session.execute(select(func.count()).select_from(Node).where(Node.run_id == run_id))
    ).scalar_one()
    nodes_completed = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "completed")
        )
    ).scalar_one()
    nodes_failed = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "failed")
        )
    ).scalar_one()
    artifacts_total = (
        await session.execute(
            select(func.count(Artifact.id))
            .select_from(Artifact)
            .join(Node, Artifact.node_id == Node.id)
            .where(Node.run_id == run_id)
        )
    ).scalar_one()
    events_total = (
        await session.execute(select(func.count()).select_from(Event).where(Event.run_id == run_id))
    ).scalar_one()

    duration_ms = None
    started = getattr(run, "started_at", None)
    ended = getattr(run, "ended_at", None)
    if started and ended:
        duration_ms = int((ended - started).total_seconds() * 1000)

    return RunSummaryOut(
        nodes_total=nodes_total,
        nodes_completed=nodes_completed,
        nodes_failed=nodes_failed,
        artifacts_total=artifacts_total,
        events_total=events_total,
        duration_ms=duration_ms,
    )
