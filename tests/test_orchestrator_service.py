import asyncio
import json
import os
from pathlib import Path

import pytest

from apps.orchestrator.service import OrchestratorService
from core.storage.file_adapter import FileAdapter
from core.storage.composite_adapter import CompositeAdapter


@pytest.fixture
def storage(tmp_path, monkeypatch):
    runs_root = tmp_path / ".runs"
    runs_root.mkdir()
    monkeypatch.setenv("RUNS_ROOT", str(runs_root))
    plans = {
        "version": "1.0",
        "plans": {
            "p1": {
                "title": "Test",
                "plan": [
                    {"id": "n1", "title": "A", "llm": {"provider": "openai", "model": "x"}},
                    {"id": "n2", "title": "B", "deps": ["n1"], "llm": {"provider": "openai", "model": "x"}},
                ],
            }
        },
    }
    plan_path = tmp_path / "plans.graph"
    plan_path.write_text(json.dumps(plans))
    monkeypatch.chdir(tmp_path)
    return CompositeAdapter([FileAdapter(str(runs_root))])


@pytest.mark.asyncio
async def test_start(storage, monkeypatch):
    calls = []

    async def fake_agent(node):
        calls.append(node.id)
        return {"markdown": node.id, "llm": {"provider": "openai", "model_used": "x", "prompts": {"final": node.llm.get("prompt", "")}}}

    monkeypatch.setattr("apps.orchestrator.executor.agent_runner", fake_agent)
    svc = OrchestratorService(storage)
    run_id = await svc.start("p1")
    await svc.wait()
    assert calls == ["n1", "n2"]
    side = json.loads((Path(os.getenv("RUNS_ROOT")) / run_id / "nodes" / "n1" / "artifact_n1.llm.json").read_text())
    assert side["dry_run"] is False


@pytest.mark.asyncio
async def test_dry_run(storage, monkeypatch):
    calls = []

    async def fake_agent(node):
        calls.append(node.id)
        return {"markdown": node.id, "llm": {"provider": "openai", "model_used": "x"}}

    monkeypatch.setattr("apps.orchestrator.executor.agent_runner", fake_agent)
    svc = OrchestratorService(storage)
    run_id = await svc.start("p1", dry_run=True)
    await svc.wait()
    assert calls == []
    side = json.loads((Path(os.getenv("RUNS_ROOT")) / run_id / "nodes" / "n1" / "artifact_n1.llm.json").read_text())
    assert side["dry_run"] is True


@pytest.mark.asyncio
async def test_override(storage, monkeypatch):
    async def fake_agent(node):
        return {"markdown": node.id, "llm": {"provider": "openai", "model_used": "x", "prompts": {"final": node.llm.get("prompt", "")}}}

    monkeypatch.setattr("apps.orchestrator.executor.agent_runner", fake_agent)
    svc = OrchestratorService(storage)
    svc.override("n1", prompt="OVR")
    run_id = await svc.start("p1")
    await svc.wait()
    side = json.loads((Path(os.getenv("RUNS_ROOT")) / run_id / "nodes" / "n1" / "artifact_n1.llm.json").read_text())
    assert side["prompt"] == "OVR"


@pytest.mark.asyncio
async def test_pause_resume_skip(storage, monkeypatch):
    calls = []

    async def fake_agent(node):
        calls.append(node.id)
        await asyncio.sleep(0.01)
        return {"markdown": node.id, "llm": {"provider": "openai", "model_used": "x"}}

    monkeypatch.setattr("apps.orchestrator.executor.agent_runner", fake_agent)
    svc = OrchestratorService(storage)
    await svc.pause()
    run_id = await svc.start("p1")
    svc.skip("n2")
    await svc.resume()
    await svc.wait()
    assert calls == ["n1"]
    side = json.loads((Path(os.getenv("RUNS_ROOT")) / run_id / "nodes" / "n2" / "artifact_n2.llm.json").read_text())
    assert side["dry_run"] is True
