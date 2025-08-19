import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.orchestrator.main import parse_args
from core.planning.task_graph import TaskGraph


def test_parse_args_acceptance_list():
    args = parse_args([])
    assert args.acceptance == ["Un plan séquencé avec sous-tâches claires."]

    args = parse_args(["--acceptance", "c1", "--acceptance", "c2"])
    assert args.acceptance == ["c1", "c2"]


def test_task_graph_string_fields_to_lists():
    plan = {
        "plan": [
            {"id": "n0", "title": "root"},
            {
                "id": "n1",
                "title": "T1",
                "deps": "n0",
                "acceptance": "crit",
                "risks": "r1",
                "assumptions": "a1",
                "notes": "n1",
            },
        ]
    }
    dag = TaskGraph.from_plan(plan)
    node = dag.nodes["n1"]
    assert node.deps == ["n0"]
    assert node.acceptance == ["crit"]
    assert node.risks == ["r1"]
    assert node.assumptions == ["a1"]
    assert node.notes == ["n1"]
