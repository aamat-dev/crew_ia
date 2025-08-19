import json
import sys

import pytest

from core.llm.providers.base import LLMResponse
import apps.orchestrator.main as orch


def test_run_supervisor_integration(tmp_path, monkeypatch):
    runs_root = tmp_path / ".runs"
    monkeypatch.setenv("RUNS_ROOT", str(runs_root))

    async def fake_run_llm(req, primary=None, fallback_order=None):
        plan = {
            "decompose": False,
            "plan": [
                {
                    "id": "n1",
                    "title": "T1",
                    "type": "execute",
                    "suggested_agent_role": "Writer_FR",
                    "deps": [],
                }
            ],
        }
        return LLMResponse(text=json.dumps(plan))

    async def fake_agent_runner(node, storage):
        await storage.save_artifact(node_id=node.id, content="ok", ext=".md")
        return "artifact"

    monkeypatch.setattr("core.llm.runner.run_llm", fake_run_llm)
    monkeypatch.setattr("core.agents.supervisor.run_llm", fake_run_llm)
    import apps.orchestrator.executor as ex
    monkeypatch.setattr(ex, "agent_runner", fake_agent_runner)

    argv = ["prog", "--use-supervisor", "--title", "Demo"]
    monkeypatch.setattr(sys, "argv", argv)

    orch.main()

    runs = [p for p in runs_root.iterdir() if p.is_dir()]
    assert runs
    plan_file = runs[0] / "plan.json"
    assert plan_file.exists()
    data = json.loads(plan_file.read_text())
    assert data["plan"]
