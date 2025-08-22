import json

import pytest
from pydantic import ValidationError

from core.agents.schemas import (
    SupervisorPlan,
    parse_manager_json,
    parse_supervisor_json,
)


def test_supervisor_json_valid():
    data = {
        "plan": [
            {
                "id": "a",
                "title": "A",
                "type": "task",
                "suggested_agent_role": "Writer",
            },
            {
                "id": "b",
                "title": "B",
                "type": "task",
                "suggested_agent_role": "Writer",
                "deps": ["a"],
            },
        ]
    }
    plan = parse_supervisor_json(json.dumps(data))
    assert isinstance(plan, SupervisorPlan)
    assert len(plan.plan) == 2


def test_supervisor_json_unknown_dep():
    data = {
        "plan": [
            {
                "id": "a",
                "title": "A",
                "type": "task",
                "suggested_agent_role": "Writer",
            },
            {
                "id": "b",
                "title": "B",
                "type": "task",
                "suggested_agent_role": "Writer",
                "deps": ["c"],
            },
        ]
    }
    with pytest.raises(ValidationError):
        parse_supervisor_json(json.dumps(data))


def test_supervisor_json_cycle():
    data = {
        "plan": [
            {
                "id": "a",
                "title": "A",
                "type": "task",
                "suggested_agent_role": "Writer",
                "deps": ["b"],
            },
            {
                "id": "b",
                "title": "B",
                "type": "task",
                "suggested_agent_role": "Writer",
                "deps": ["a"],
            },
        ]
    }
    with pytest.raises(ValidationError):
        parse_supervisor_json(json.dumps(data))


def test_supervisor_json_duplicate_ids():
    data = {
        "plan": [
            {
                "id": "a",
                "title": "A",
                "type": "task",
                "suggested_agent_role": "Writer",
            },
            {
                "id": "a",
                "title": "A2",
                "type": "task",
                "suggested_agent_role": "Writer",
            },
        ]
    }
    with pytest.raises(ValidationError):
        parse_supervisor_json(json.dumps(data))


def test_supervisor_json_backward_compat():
    plan_data = {
        "plan": [
            {
                "id": "a",
                "title": "A",
                "type": "execute",
                "suggested_agent_role": "Writer",
            }
        ]
    }
    plan = parse_supervisor_json(json.dumps(plan_data))
    assert plan.plan[0].type == "task"

    manager_data = {
        "assignments": [{"node_id": "a", "agent": "X"}],
        "quality_checks": ["qc"],
    }
    out = parse_manager_json(json.dumps(manager_data))
    assert out.assignments[0].agent_role == "X"
