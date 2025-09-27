from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import (
    get_session,
    strict_api_key_auth,
    read_timezone,
    to_tz,
)
from ..schemas_base import Page, AuditLogOut
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order
from core.storage.db_models import AuditLog  # type: ignore

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(strict_api_key_auth)])

ORDERABLE_FIELDS = {
    "created_at": AuditLog.created_at,
    "action": AuditLog.action,
}


@router.get("", response_model=Page[AuditLogOut])
async def list_audit_logs(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz=Depends(read_timezone),
    pagination: PaginationParams = Depends(pagination_params),
    run_id: Optional[UUID] = Query(None),
    node_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
):
    filters = []
    if run_id:
        filters.append(AuditLog.run_id == run_id)
    if node_id:
        filters.append(AuditLog.node_id == node_id)
    if action:
        filters.append(AuditLog.action == action)
    if actor_role:
        filters.append(AuditLog.actor_role == actor_role)
    if actor:
        filters.append(AuditLog.actor == actor)
    if source:
        filters.append(AuditLog.source == source)

    if not filters:
        raise HTTPException(status_code=400, detail="run_id ou node_id requis pour consulter les journaux")

    base = select(AuditLog)
    if filters:
        base = base.where(and_(*filters))

    total_stmt = select(func.count(AuditLog.id)).select_from(AuditLog)
    if filters:
        total_stmt = total_stmt.where(and_(*filters))
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = apply_order(
        base,
        pagination.order_by,
        pagination.order_dir,
        ORDERABLE_FIELDS,
        "-created_at",
    ).limit(pagination.limit).offset(pagination.offset)

    rows = (await session.execute(stmt)).scalars().all()
    items = [
        AuditLogOut(
            id=row.id,
            run_id=row.run_id,
            node_id=row.node_id,
            source=row.source,
            action=row.action,
            actor_role=row.actor_role,
            actor=row.actor,
            request_id=row.request_id,
            metadata=row.payload,
            created_at=to_tz(row.created_at, tz),
        )
        for row in rows
    ]

    links = set_pagination_headers(response, request, total, pagination.limit, pagination.offset)

    return Page[AuditLogOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )
