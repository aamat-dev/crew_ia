from __future__ import annotations

from typing import List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from backend.core.models import PlanStatus


class PlanNode(BaseModel):
    """Noeud du plan (compatible PDF et orchestrateur)."""

    id: str
    title: str
    deps: List[str] = Field(default_factory=list)
    suggested_agent_role: str
    acceptance: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class PlanGraph(BaseModel):
    """Représentation du plan standardisée.

    - Sortie standard: { version, plan: [PlanNode], edges: [...] }
    - Entrée tolérante: accepte aussi { nodes: [...] } et mappe vers plan.
    """

    model_config = ConfigDict(extra="allow")

    version: str = "1.0"
    plan: List[PlanNode] = Field(default_factory=list)
    edges: List[Dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _accept_nodes_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Compat: si 'plan' absent mais 'nodes' présent, mappe nodes -> plan
            if "plan" not in data and isinstance(data.get("nodes"), list):
                data = dict(data)
                data["plan"] = data.get("nodes") or []
        return data


class PlanGenerationResult(BaseModel):
    graph: PlanGraph
    status: PlanStatus


class PlanCreateResponse(BaseModel):
    plan_id: UUID
    status: PlanStatus
    graph: PlanGraph
