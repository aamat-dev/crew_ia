import json, pytest
from pathlib import Path
from core.agents.executor_llm import agent_runner
from core.agents.schemas import PlanNodeModel
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod

@pytest.mark.asyncio
async def test_sidecar_prompt_truncation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="ok", provider="p", model_used="m")
    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)

    class DummyStorage:
        async def save_artifact(self, node_id, content, ext=".md"):
            Path(f"artifact_{node_id}{ext}").write_text(content, encoding="utf-8")

    long = "x" * 5000
    node = PlanNodeModel(id="n1", title=long, type="execute", suggested_agent_role="Writer_FR",
                         acceptance=[long], notes=[long])
    await agent_runner(node, DummyStorage())

    # executor_llm writes a sidecar named artifact_<id>.llm.json in CWD
    candidates = list(Path(".").glob("artifact_*.llm.json"))
    assert candidates, "no sidecar found"
    sidecar = json.loads(candidates[0].read_text(encoding="utf-8"))
    assert len(sidecar["prompts"]["system"]) <= 800
    assert len(sidecar["prompts"]["user"]) <= 800
