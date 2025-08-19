import json
from pathlib import Path
import pytest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.agents.executor_llm import agent_runner
from core.agents.schemas import PlanNodeModel
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod

@pytest.mark.asyncio
async def test_agent_routing_writer(monkeypatch, tmp_path):
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="texte", provider="p", model_used="m")
    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)
    monkeypatch.chdir(tmp_path)

    class DummyStorage:
        async def save_artifact(self, node_id, content, ext=".md"):
            Path(f"artifact_{node_id}{ext}").write_text(content, encoding="utf-8")

    node = PlanNodeModel(id="w1", title="Titre", type="execute", suggested_agent_role="Writer_FR")
    path = await agent_runner(node, DummyStorage())
    content = Path(path).read_text(encoding="utf-8")
    assert content.startswith("# ")
    side = json.loads(Path(path.replace('.md','.llm.json')).read_text(encoding="utf-8"))
    assert side["provider"] == "p"
    assert side["model"] == "m"
