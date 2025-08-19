import pytest
from core.planning import planner

def test_cycle_detection_raises():
    plan = {"nodes": [{"id": "n1","role":"Writer_FR","deps":["n2"]},{"id":"n2","role":"Researcher","deps":["n1"]}]}
    with pytest.raises(Exception):
        planner.TaskGraph.from_plan(plan)
