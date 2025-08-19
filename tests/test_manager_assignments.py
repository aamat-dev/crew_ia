import pytest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
