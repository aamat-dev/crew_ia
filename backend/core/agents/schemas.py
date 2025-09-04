from typing import List, Literal
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field, model_validator


NodeType = Literal["task", "manage", "synthesis"]


class PlanNode(BaseModel):
    """Noeud du plan supervisé."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    title: str
    type: NodeType
    suggested_agent_role: str
    deps: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def map_execute(cls, data: dict):
        """Convertir l'ancien type 'execute' en 'task' pour compatibilité."""
        if isinstance(data, dict) and data.get("type") == "execute":
            data = dict(data)
            data["type"] = "task"
        return data


# Compatibilité ascendante
PlanNodeModel = PlanNode


class SupervisorPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    decompose: bool = False
    plan: List[PlanNode]

    @model_validator(mode="after")
    def validate_graph(self) -> "SupervisorPlan":
        all_ids = [n.id for n in self.plan]
        ids = set(all_ids)
        if len(ids) != len(all_ids):
            counts = Counter(all_ids)
            dup = [node_id for node_id, count in counts.items() if count > 1]
            raise ValueError(f"Duplicate node id(s) detected: {dup}")
        for n in self.plan:
            missing = set(n.deps) - ids
            if missing:
                raise ValueError(f"Unknown dep in node {n.id}: {missing}")
            if not n.suggested_agent_role.strip():
                raise ValueError(f"Missing role in node {n.id}")
        indeg = {n.id: 0 for n in self.plan}
        outgoing = {n.id: [] for n in self.plan}
        for n in self.plan:
            for d in n.deps:
                indeg[n.id] += 1
                outgoing[d].append(n.id)
        zero = [k for k, v in indeg.items() if v == 0]
        visited = 0
        while zero:
            u = zero.pop()
            visited += 1
            for v in outgoing[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    zero.append(v)
        if visited != len(self.plan):
            raise ValueError("Cycle detected")
        return self


class ManagerAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    node_id: str
    agent_role: str = Field(alias="agent")
    tooling: List[str] = Field(default_factory=list)


class ManagerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    assignments: List[ManagerAssignment]
    quality_checks: List[str] = Field(min_length=1)
    integration_notes: str = ""


class AgentSpec(BaseModel):
    """Spécification d'un agent disponible pour l'exécution."""

    model_config = ConfigDict(extra="forbid", strict=True)

    role: str
    system_prompt: str
    provider: str
    model: str
    tools: List[str] = Field(default_factory=list)


def parse_supervisor_json(data: str) -> SupervisorPlan:
    return SupervisorPlan.model_validate_json(data)


def parse_manager_json(data: str) -> ManagerOutput:
    return ManagerOutput.model_validate_json(data)
