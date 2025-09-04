from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import get_session, strict_api_key_auth, read_role, require_role, require_request_id
from ..schemas_base import (
    Page,
    AgentOut,
    AgentCreate,
    AgentUpdate,
    AgentMatrixOut,
)
from ..schemas.prompting import RecruitRequest, RecruitResponse
from ..services.recruit_service import RecruitService
from ..models.agent import Agent, AgentModelsMatrix
from backend.api.utils.pagination import PaginationParams, pagination_params, set_pagination_headers
from ..ordering import apply_order

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(strict_api_key_auth)])

ORDERABLE = {"created_at": Agent.created_at, "name": Agent.name}


@router.get("", response_model=Page[AgentOut])
async def list_agents(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(pagination_params),
    role: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    _: str = Depends(read_role),
):
    where = []
    if role:
        where.append(Agent.role == role)
    if domain:
        where.append(Agent.domain == domain)
    if is_active is not None:
        where.append(Agent.is_active == is_active)

    base = select(Agent).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(Agent.id)).where(and_(*where))
        )
    ).scalar_one()
    stmt = apply_order(
        base,
        pagination.order_by,
        pagination.order_dir,
        ORDERABLE,
        "-created_at",
    ).limit(pagination.limit).offset(pagination.offset)
    rows = (await session.execute(stmt)).scalars().all()
    items = [AgentOut.model_validate(r) for r in rows]
    links = set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[AgentOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )


@router.post("", response_model=AgentOut, status_code=201, dependencies=[Depends(require_role("editor", "admin"))])
async def create_agent(
    payload: AgentCreate,
    session: AsyncSession = Depends(get_session),
    _req_id: str = Depends(require_request_id),
):
    agent = Agent(**payload.model_dump())
    session.add(agent)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="agent name exists")
    await session.refresh(agent)
    return AgentOut.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentOut, dependencies=[Depends(require_role("editor", "admin"))])
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    session: AsyncSession = Depends(get_session),
    _req_id: str = Depends(require_request_id),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(agent, k, v)
    agent.version += 1
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return AgentOut.model_validate(agent)


@router.post("/{agent_id}/deactivate", status_code=204, dependencies=[Depends(require_role("editor", "admin"))])
async def deactivate_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    _req_id: str = Depends(require_request_id),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="not found")
    agent.is_active = False
    agent.version += 1
    session.add(agent)
    await session.commit()
    return Response(status_code=204)


# -------- models matrix ----------------------------------------------------

M_ORDERABLE = {"created_at": AgentModelsMatrix.created_at}


@router.get("/models-matrix", response_model=Page[AgentMatrixOut])
async def list_models_matrix(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(pagination_params),
    role: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    _: str = Depends(read_role),
):
    where = []
    if role:
        where.append(AgentModelsMatrix.role == role)
    if domain:
        where.append(AgentModelsMatrix.domain == domain)
    base = select(AgentModelsMatrix).where(and_(*where))
    total = (
        await session.execute(
            select(func.count(AgentModelsMatrix.id)).where(and_(*where))
        )
    ).scalar_one()
    stmt = apply_order(
        base,
        pagination.order_by,
        pagination.order_dir,
        M_ORDERABLE,
        "-created_at",
    ).limit(pagination.limit).offset(pagination.offset)
    rows = (await session.execute(stmt)).scalars().all()
    items = [AgentMatrixOut.model_validate(r) for r in rows]
    links = set_pagination_headers(
        response, request, total, pagination.limit, pagination.offset
    )
    return Page[AgentMatrixOut](
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        links=links or None,
    )


@router.post("/recruit", response_model=RecruitResponse, status_code=201, dependencies=[Depends(require_role("editor", "admin"))])
async def recruit_agent_endpoint(
    payload: RecruitRequest,
    session: AsyncSession = Depends(get_session),
    request_id: str = Depends(require_request_id),
):
    data = await RecruitService.recruit(session, payload, request_id)
    return data
