from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import List, Optional, Literal, Dict, Any, Set

NodeType = Literal["manage","execute"]

class PlanNodeModel(BaseModel):
    id: str
    title: str
    type: NodeType
    suggested_agent_role: str
    acceptance: List[str] = Field(default_factory=list)
    deps: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class SupervisorPlan(BaseModel):
    decompose: bool
    plan: List[PlanNodeModel]

    @model_validator(mode="after")
    def no_cycles_and_roles(self) -> "SupervisorPlan":
        ids = {n.id for n in self.plan}
        # deps must exist
        for n in self.plan:
            assert all(d in ids for d in n.deps), "Unknown dep in node "+n.id
            assert n.suggested_agent_role.strip(), "Missing role in node "+n.id
        # cycle check
        indeg = {n.id:0 for n in self.plan}
        for n in self.plan:
            for d in n.deps: indeg[n.id]+=1
        zero = [k for k,v in indeg.items() if v==0]
        visited = 0
        nodes_by_id = {n.id:n for n in self.plan}
        while zero:
            u = zero.pop()
            visited += 1
            for v in (x.id for x in self.plan if u in x.deps):
                indeg[v]-=1
                if indeg[v]==0: zero.append(v)
        assert visited==len(self.plan), "Cycle detected"
        return self

class ManagerAssignment(BaseModel):
    node_id: str
    agent: str
    tooling: List[str] = Field(default_factory=list)

class ManagerOutput(BaseModel):
    assignments: List[ManagerAssignment]
    quality_checks: List[str]
    integration_notes: str = ""

# Utilitaires d’analyse/parse strict JSON
def parse_supervisor_json(data: str) -> SupervisorPlan:
    return SupervisorPlan.model_validate_json(data)

def parse_manager_json(data: str) -> ManagerOutput:
    return ManagerOutput.model_validate_json(data)
