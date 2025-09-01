from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from api.fastapi_app.deps import strict_api_key_auth
from app.schemas.node_actions import NodeActionRequest, NodeActionResponse
from app.services import orchestrator_adapter

router = APIRouter(prefix="/nodes", tags=["nodes"], dependencies=[Depends(strict_api_key_auth)])


@router.patch(
    "/{node_id}",
    response_model=NodeActionResponse,
    response_model_exclude_none=True,
)
async def node_action_route(node_id: UUID, action: NodeActionRequest) -> NodeActionResponse:
    payload = action.model_dump(exclude={"action"}, exclude_none=True)
    result = await orchestrator_adapter.node_action(node_id, action.action, payload)
    return NodeActionResponse(node_id=node_id, **result)
