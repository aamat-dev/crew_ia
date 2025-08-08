import pytest
from core.planning.task_graph import TaskGraph

def test_dag_ok():
    plan = {"plan": [
        {"id":"n1","deps":[]},
        {"id":"n2","deps":["n1"]},
    ]}
    dag = TaskGraph.from_plan(plan)
    roots = list(dag.roots())
    assert roots and roots[0].id == "n1"

def test_dag_cycle_ko():
    plan = {"plan": [
        {"id":"n1","deps":["n2"]},
        {"id":"n2","deps":["n1"]},
    ]}
    with pytest.raises(ValueError):
        TaskGraph.from_plan(plan)
