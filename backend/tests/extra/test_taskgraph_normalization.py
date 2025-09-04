from core.planning.task_graph import TaskGraph

def test_taskgraph_normalization_lists():
    plan = {
        "plan": [{
            "id": "n1",
            "title": "A",
            "type": "execute",
            "suggested_agent_role": "Researcher",
            "acceptance": "crit",
            "deps": None,
            "risks": 0,
            "assumptions": ["x", None, "y"],
            "notes": True
        }]
    }
    dag = TaskGraph.from_plan(plan)
    a = dag.nodes["n1"]
    assert a.acceptance == ["crit"]
    assert a.deps == []
    assert a.risks == ["0"]
    assert a.assumptions == ["x","y"]
    # Current behavior: booleans are coerced to strings
    assert a.notes == ["True"]
