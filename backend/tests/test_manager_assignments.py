import pytest
from pydantic import ValidationError

from core.agents.manager import run_manager
from core.agents.schemas import PlanNodeModel
from core.llm.providers.base import LLMResponse
import core.agents.manager as manager_mod

@pytest.mark.asyncio
async def test_manager_assignments(monkeypatch):
    async def fake_run_llm(req, primary=None, fallback_order=None):
        text = '{"assignments":[{"node_id":"a","agent":"Writer_FR","tooling":[]}],"quality_checks":["qc"]}'
        return LLMResponse(text=text, provider="p", model_used="m")
    monkeypatch.setattr(manager_mod, "run_llm", fake_run_llm)
    nodes = [
        PlanNodeModel(id="a", title="A", type="execute", suggested_agent_role="Writer_FR"),
        PlanNodeModel(id="b", title="B", type="execute", suggested_agent_role="Writer_FR"),
    ]
    out = await run_manager(nodes)
    ids = {n.id for n in nodes}
    for a in out.assignments:
        assert a.node_id in ids
    assert out.quality_checks


@pytest.mark.asyncio
async def test_manager_assignments_reprompt(monkeypatch):
    calls = {"n": 0}

    async def fake_run_llm(req, primary=None, fallback_order=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return LLMResponse(text="oops")
        text = '{"assignments":[{"node_id":"a","agent":"Writer_FR","tooling":[]}],"quality_checks":["qc"]}'
        return LLMResponse(text=text)

    monkeypatch.setattr(manager_mod, "run_llm", fake_run_llm)
    nodes = [PlanNodeModel(id="a", title="A", type="execute", suggested_agent_role="Writer_FR")]
    out = await run_manager(nodes)
    assert calls["n"] == 2
    assert out.assignments[0].node_id == "a"


@pytest.mark.asyncio
async def test_manager_assignments_fallback(monkeypatch):
    calls = {"n": 0}

    async def fake_run_llm(req, primary=None, fallback_order=None):
        calls["n"] += 1
        return LLMResponse(text="oops")

    monkeypatch.setattr(manager_mod, "run_llm", fake_run_llm)
    nodes = [PlanNodeModel(id="a", title="A", type="execute", suggested_agent_role="Writer_FR")]

    with pytest.raises(ValidationError):
        await run_manager(nodes)
    assert calls["n"] == 3
