import json

import pytest
from pydantic import ValidationError

from core.agents.schemas import (
    SupervisorPlan,
    parse_manager_json,
    parse_supervisor_json,
)
from core.agents.supervisor import run as supervisor_run
import core.agents.supervisor as supervisor_mod
from core.llm.providers.base import LLMResponse


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


@pytest.mark.asyncio
async def test_supervisor_reprompt(monkeypatch):
    calls = {"n": 0}

    async def fake_run_llm(req, primary=None, fallback_order=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return LLMResponse(text="oops")
        valid = {
            "plan": [
                {
                    "id": "a",
                    "title": "A",
                    "type": "task",
                    "suggested_agent_role": "Writer_FR",
                }
            ]
        }
        return LLMResponse(text=json.dumps(valid))

    monkeypatch.setattr(supervisor_mod.llm_runner, "run_llm", fake_run_llm)

    sup = await supervisor_run({"title": "demo"})
    assert calls["n"] == 2
    assert isinstance(sup, SupervisorPlan)
    assert sup.plan[0].id == "a"
