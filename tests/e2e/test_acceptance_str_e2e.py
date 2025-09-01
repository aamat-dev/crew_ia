from pathlib import Path
import pytest

from core.planning.task_graph import TaskGraph
from apps.orchestrator.executor import run_graph
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod


class DummyStorage:
    async def save_artifact(self, node_id, content, ext=".md"):
        Path(f"artifact_{node_id}{ext}").write_text(content, encoding="utf-8")
        return True


@pytest.mark.asyncio
async def test_acceptance_str_e2e(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = {
        "plan": [
            {
                "id": "n1",
                "title": "T1",
                "type": "execute",
                "suggested_agent_role": "Researcher",
                "acceptance": "crit",
            }
        ]
    }
    dag = TaskGraph.from_plan(plan)

    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="ok", provider="p", model_used="m")

    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)

    res = await run_graph(dag, DummyStorage(), "run1")
    assert res["status"] == "succeeded"
    assert Path("artifact_n1.md").exists()
