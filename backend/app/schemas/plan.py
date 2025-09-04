from __future__ import annotations

from typing import List, Dict
from uuid import UUID

from pydantic import BaseModel, Field

from backend.core.models import PlanStatus


class PlanNode(BaseModel):
    """Noeud de plan généré par le superviseur."""

    id: str
    title: str
    deps: List[str] = Field(default_factory=list)
    suggested_agent_role: str
    acceptance: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class PlanGraph(BaseModel):
    """Représentation DAG v1.0."""

    version: str = "1.0"
    nodes: List[PlanNode] = Field(default_factory=list)
    edges: List[Dict[str, str]] = Field(default_factory=list)


class PlanGenerationResult(BaseModel):
    graph: PlanGraph
    status: PlanStatus


class PlanCreateResponse(BaseModel):
    plan_id: UUID
    status: PlanStatus
    graph: PlanGraph
