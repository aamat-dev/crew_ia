from pathlib import Path
from typing import List
import json

from core.agents.supervisor import run_supervisor
from core.agents.schemas import PlanNodeModel
from core.planning.task_graph import PlanNode

async def plan_from_task(task_input: str, run_dir: str = ".") -> List[PlanNode]:
    sup = await run_supervisor(task_input)
    nodes: List[PlanNode] = []
    for n in sup.plan:
        nodes.append(
            PlanNode(
                id=n.id,
                title=n.title,
                type=n.type,
                suggested_agent_role=n.suggested_agent_role,
                acceptance=n.acceptance,
                deps=n.deps,
                risks=n.risks,
                assumptions=n.assumptions,
                notes=n.notes,
            )
        )
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    Path(run_dir, "plan.json").write_text(
        sup.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return nodes
