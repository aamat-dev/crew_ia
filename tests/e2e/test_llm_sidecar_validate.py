from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

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
async def test_llm_sidecar_validate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_id = str(uuid4())
    plan = {
        "plan": [
            {
                "id": "n1",
                "title": "T1",
                "type": "execute",
                "suggested_agent_role": "Researcher",
            }
        ]
    }
    dag = TaskGraph.from_plan(plan)
    dag.nodes["n1"].db_id = uuid4()

    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="ok", provider="openai", model_used="m")

    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)

    res = await run_graph(dag, DummyStorage(), run_id)
    assert res["status"] == "succeeded"

    script = Path(__file__).resolve().parents[2] / "tools" / "validate_sidecars.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--since", run_id],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert re.search(r"OK:\s*[1-9]\d*", proc.stdout)
