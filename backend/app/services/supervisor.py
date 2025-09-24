from __future__ import annotations

import os
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
        # Fallback dev: optionnellement, proposer un plan minimal en mode draft
        if str(os.getenv("PLAN_FALLBACK_DRAFT", "")).strip().lower() in {"1", "true", "yes", "on"}:
            graph = PlanGraph(
                nodes=[
                    PlanNode(
                        id="n1",
                        title=task.title or "Tâche",
                        deps=[],
                        suggested_agent_role="executor",
                        acceptance=["doit produire un JSON valide"],
                        risks=[],
                        assumptions=[],
                        notes=[],
                    )
                ],
                edges=[],
            )
            return PlanGenerationResult(graph=graph, status=PlanStatus.draft)
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
    status = PlanStatus.draft if nodes else (
        PlanStatus.draft if str(os.getenv("PLAN_FALLBACK_DRAFT", "")).strip().lower() in {"1", "true", "yes", "on"} else PlanStatus.invalid
    )
    if status is PlanStatus.draft and not nodes:
        graph = PlanGraph(
            nodes=[
                PlanNode(
                    id="n1",
                    title=task.title or "Tâche",
                    deps=[],
                    suggested_agent_role="executor",
                    acceptance=["doit produire un JSON valide"],
                    risks=[],
                    assumptions=[],
                    notes=[],
                )
            ],
            edges=[],
        )
    return PlanGenerationResult(graph=graph, status=status)
