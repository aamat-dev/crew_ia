import pytest
from core.agents.executor_llm import agent_runner
from core.agents.schemas import PlanNodeModel
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod


@pytest.mark.asyncio
async def test_sidecar_prompt_truncation(tmp_path, monkeypatch):
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="ok", provider="p", model_used="m")
    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)

    long = "x" * 5000
    node = PlanNodeModel(
        id="n1",
        title=long,
        type="execute",
        suggested_agent_role="Writer_FR",
        acceptance=[long],
        notes=[long],
    )
    res = await agent_runner(node)
    assert len(res["llm"]["prompts"]["final"]) <= 800
