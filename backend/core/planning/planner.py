from pathlib import Path
import json

from core.agents.supervisor import run
from core.planning.task_graph import TaskGraph


async def plan_from_task(task_input: str, run_dir: str = ".") -> TaskGraph:
    sup = await run(json.loads(task_input))

    Path(run_dir).mkdir(parents=True, exist_ok=True)
    Path(run_dir, "plan.json").write_text(
        sup.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8"
    )

    graph = TaskGraph.from_plan(sup.model_dump())
    return graph
