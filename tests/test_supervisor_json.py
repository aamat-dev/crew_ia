import pytest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pydantic import ValidationError
from core.agents.schemas import parse_supervisor_json, SupervisorPlan

def test_supervisor_json_valid():
    data = '{"decompose": true, "plan": []}'
    plan = parse_supervisor_json(data)
    assert isinstance(plan, SupervisorPlan)

def test_supervisor_json_invalid():
    with pytest.raises(ValidationError):
        parse_supervisor_json('{"bad":1}')
