from __future__ import annotations

import logging
from core import log as _core_log  # noqa: F401
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from api.fastapi_app.deps import strict_api_key_auth
from app.schemas.node_actions import NodeActionRequest, NodeActionResponse
from app.services import orchestrator_adapter

router = APIRouter(prefix="/nodes", tags=["nodes"], dependencies=[Depends(strict_api_key_auth)])

log = logging.getLogger("api.node_actions")


@router.patch(
    "/{node_id}",
    response_model=NodeActionResponse,
    response_model_exclude_none=True,
)
async def node_action_route(
    node_id: UUID, action: NodeActionRequest, request: Request
) -> NodeActionResponse:
    payload = action.model_dump(exclude={"action"}, exclude_none=True, by_alias=True)
    result = await orchestrator_adapter.node_action(node_id, action.action, payload)

    req_id = getattr(request.state, "request_id", None)
    log.info(
        "node action",
        extra={
            "run_id": str(result.get("run_id")) if result.get("run_id") else None,
            "node_id": str(node_id),
            "request_id": req_id,
            "action": action.action,
        },
    )

    filtered = {
        k: v for k, v in result.items() if k in {"status_after", "sidecar_updated"} and v is not None
    }
    return NodeActionResponse(node_id=node_id, **filtered)
