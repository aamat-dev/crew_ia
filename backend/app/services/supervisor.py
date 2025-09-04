from __future__ import annotations

from typing import List

from backend.core.models import Task
from backend.core.models import PlanStatus
from backend.api.schemas.plan import (
    PlanNode,
    PlanGraph,
    PlanGenerationResult,
)
from core.agents import supervisor


async def generate_plan(task: Task) -> PlanGenerationResult:
    """Génère un plan DAG via le superviseur."""

    try:
        sup_plan = await supervisor.run(
            {"title": task.title, "description": task.description or ""}
        )
    except Exception:
        return PlanGenerationResult(graph=PlanGraph(), status=PlanStatus.invalid)

    nodes: List[PlanNode] = []
    edges = []
    for n in sup_plan.plan:
        nodes.append(
            PlanNode(
                id=n.id,
                title=n.title,
                deps=n.deps,
                suggested_agent_role=n.suggested_agent_role,
                acceptance=n.acceptance,
                risks=n.risks,
                assumptions=n.assumptions,
                notes=n.notes,
            )
        )
        for dep in n.deps:
            edges.append({"source": dep, "target": n.id})

    graph = PlanGraph(nodes=nodes, edges=edges)
    status = PlanStatus.draft if nodes else PlanStatus.invalid
    return PlanGenerationResult(graph=graph, status=status)
