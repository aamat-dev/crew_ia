from core.planning import planner

def test_taskgraph_normalization_lists():
    plan = {"nodes": [{"id": "n1", "role": "Writer_FR", "deps": "x"}]}
    tg = planner.TaskGraph.from_plan(plan)
    assert isinstance(tg.nodes[0].deps, list)
