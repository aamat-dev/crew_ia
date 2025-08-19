"""
task_graph.py — Transforme un plan JSON en DAG exploitable.
- Valide l'absence de cycles (graph acyclique).
- Vérifie que les dépendances pointent vers des nœuds existants.
- Construit les successeurs pour faciliter l'exécution.
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class PlanNode:
    """
    Représentation d'un nœud du plan (une sous-tâche).
    Note: on évite d’en faire un type hashable car il contient des listes (mutable).
    """
    id: str
    title: str = ""
    description: str = ""
    type: str = "task"
    deps: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    suggested_agent_role: str = ""
    risks: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    succ: list = field(default_factory=list)
    llm: Dict[str, Any] = field(default_factory=dict)   # <-- NEW          # successeurs (remplis après construction du graphe)


class TaskGraph:
    """
    Objet enveloppant le graphe NetworkX et un index {id -> PlanNode}.
    """
    def __init__(self, nodes: list[PlanNode]):
        self.nodes = {n.id: n for n in nodes}  # accès direct par id
        self._g = nx.DiGraph()

        # 1) Ajouter tous les nœuds
        for n in nodes:
            self._g.add_node(n.id)

        # 2) Ajouter les arêtes (dépendances)
        for n in nodes:
            for d in n.deps:
                if d not in self.nodes:
                    raise ValueError(f"Dependency {d} not in nodes")
                # arête d -> n : on ne peut exécuter n qu'une fois d terminé
                self._g.add_edge(d, n.id)

        # 3) Vérifier que le graphe est acyclique
        if not nx.is_directed_acyclic_graph(self._g):
            raise ValueError("Plan is not a DAG")

        # 4) Initialiser les successeurs (facilite l'exécution)
        for a, b in self._g.edges():
            self.nodes[a].succ.append(self.nodes[b])

    @classmethod
    def from_plan(cls, plan: dict):
        """
        Construit un TaskGraph à partir d'un dict JSON de plan :
        {
          "plan": [
            {"id":"n1","title":"...","deps":[],"acceptance":"..."},
            {"id":"n2","deps":["n1"], ...}
          ]
        }
        """
        nodes = [
            PlanNode(
                id=p["id"],
                title=p.get("title", ""),
                description=p.get("description", ""),
                type=p.get("type", "task"),
                deps=p.get("deps", []),
                acceptance=p.get("acceptance", []),
                suggested_agent_role=p.get("suggested_agent_role", ""),
                risks=p.get("risks", []),
                assumptions=p.get("assumptions", []),
                notes=p.get("notes", []),
                llm=p.get("llm", {}) or {},                     # <-- NEW
            )
            for p in plan.get("plan", [])
        ]
        return cls(nodes)

    def roots(self):
        """
        Génère les nœuds racines (aucune dépendance entrante).
        """
        for nid in self.nodes:
            if self._g.in_degree(nid) == 0:
                yield self.nodes[nid]
