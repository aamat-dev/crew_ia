from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class AssignmentItem(BaseModel):
    node_id: str
    role: str
    agent_id: str
    llm_backend: str
    llm_model: str
    params: Optional[Dict[str, Any]] = None


class AssignmentsPayload(BaseModel):
    items: List[AssignmentItem]


class AssignmentsResponse(BaseModel):
    updated: int
    items: List[AssignmentItem]
