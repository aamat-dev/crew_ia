from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan
from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentsPayload, AssignmentsResponse
from api.fastapi_app.deps import get_db, strict_api_key_auth

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    dependencies=[Depends(strict_api_key_auth)],
)


def _plan_node_ids(plan: Plan) -> set[str]:
    nodes = plan.graph.get("plan") or []
    return {n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")}


@router.post("/{plan_id}/assignments", response_model=AssignmentsResponse, status_code=status.HTTP_200_OK)
async def upsert_assignments(
    plan_id: UUID,
    payload: AssignmentsPayload,
    db: AsyncSession = Depends(get_db),
) -> AssignmentsResponse:
    plan = await db.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    valid_ids = _plan_node_ids(plan)
    updated = 0
    out_items = []
    for item in payload.items:
        if item.node_id not in valid_ids:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unknown node_id: {item.node_id}")
        stmt = select(Assignment).where(
            Assignment.plan_id == plan_id, Assignment.node_id == item.node_id
        )
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        data = item.model_dump()
        if assignment:
            assignment.role = data["role"]
            assignment.agent_id = data["agent_id"]
            assignment.llm_backend = data["llm_backend"]
            assignment.llm_model = data["llm_model"]
            assignment.params = data.get("params")
        else:
            assignment = Assignment(plan_id=plan_id, **data)
            db.add(assignment)
        updated += 1
        out_items.append(item)
    await db.commit()
    return AssignmentsResponse(updated=updated, items=out_items)
