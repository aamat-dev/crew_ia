import os, sys, json, pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.agents.supervisor import run as supervisor_run
from core.llm.providers.base import LLMResponse
import core.llm.runner as runner_mod

@pytest.mark.asyncio
async def test_supervisor_simulation(monkeypatch):
    plan = {
        "decompose": True,
        "plan": [
            {
                "id": "n1",
                "title": "Root task",
                "type": "execute",
                "suggested_agent_role": "Writer_FR",
                "acceptance": ["ok"],
                "deps": [],
                "risks": [],
                "assumptions": [],
                "notes": []
            }
        ]
    }
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text=json.dumps(plan))
    monkeypatch.setattr(runner_mod, "run_llm", fake_run_llm)
    sup = await supervisor_run({"title":"Demo"})
    assert sup.decompose is True
    assert sup.plan and sup.plan[0].id == "n1"
