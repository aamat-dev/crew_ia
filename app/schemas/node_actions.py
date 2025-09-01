from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class NodeActionRequest(BaseModel):
    """Requête pour une action sur un nœud."""

    action: Literal["pause", "resume", "override", "skip"]
    override_prompt: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class NodeActionResponse(BaseModel):
    """Réponse après une action sur un nœud."""

    node_id: UUID
    status_after: str
    sidecar_updated: Optional[bool] = None
