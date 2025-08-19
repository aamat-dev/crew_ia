import pytest
from core.planning.task_graph import TaskGraph

def test_cycle_detection_raises():
    plan = {
        "plan": [
            {"id": "a", "title": "A", "type": "execute", "suggested_agent_role": "Researcher", "deps": ["b"]},
            {"id": "b", "title": "B", "type": "execute", "suggested_agent_role": "Writer_FR", "deps": ["a"]},
        ]
    }
    with pytest.raises(ValueError):
        TaskGraph.from_plan(plan)
