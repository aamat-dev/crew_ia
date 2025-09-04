
"""
task_graph.py — Build a DAG from a validated SupervisorPlan.
- Verifies absence of cycles.
- Verifies that dependencies reference existing nodes.
- Adds successors for convenience.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any
import networkx as nx

def _as_str_list(val) -> List[str]:
    if val is None or val is False:
        return []
    if isinstance(val, list):
        return [str(x) for x in val if x is not None]
    # allow single string or numbers to be coerced
    return [str(val)]

@dataclass
class PlanNode:
    id: str
    title: str
    type: str  # "manage" | "execute"
    suggested_agent_role: str
    acceptance: List[str] = field(default_factory=list)
    deps: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    llm: Dict[str, Any] = field(default_factory=dict)

class TaskGraph:
    def __init__(self, nodes: List[PlanNode]):
        self._g = nx.DiGraph()
        self.nodes: Dict[str, PlanNode] = {}
        for n in nodes:
            self.nodes[n.id] = n
            self._g.add_node(n.id)
        for n in nodes:
            for d in n.deps:
                if d not in self.nodes:
                    raise ValueError("Unknown dependency '{}' for node {}".format(d, n.id))
                self._g.add_edge(d, n.id)
        # ensure acyclic
        if not nx.is_directed_acyclic_graph(self._g):
            raise ValueError("Plan contains cycles")
        # precompute successors for convenience
        for nid in list(self._g.nodes):
            succ = list(self._g.successors(nid))
            setattr(self.nodes[nid], "succ", succ)

    @classmethod
    def from_plan(cls, plan: Dict[str, Any]) -> "TaskGraph":
        nodes: List[PlanNode] = []
        for p in plan.get("plan", []) or []:
            nodes.append(PlanNode(
                id=p["id"],
                title=p.get("title",""),
                type=p.get("type","execute"),
                suggested_agent_role=p.get("suggested_agent_role",""),
                acceptance=_as_str_list(p.get("acceptance")),
                deps=_as_str_list(p.get("deps")),
                risks=_as_str_list(p.get("risks")),
                assumptions=_as_str_list(p.get("assumptions")),
                notes=_as_str_list(p.get("notes")),
                llm=p.get("llm") or {}
            ))
        return cls(nodes)

    def roots(self):
        for nid in self.nodes:
            if self._g.in_degree(nid) == 0:
                yield self.nodes[nid]
