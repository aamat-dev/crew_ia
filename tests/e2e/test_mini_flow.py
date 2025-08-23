import json
from pathlib import Path
import pytest

from core.planning.task_graph import PlanNode, TaskGraph
from apps.orchestrator.executor import run_graph
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod
import apps.orchestrator.executor as orch_exec

class DummyStorage:
    async def save_artifact(self, node_id, content, ext=".md"):
        Path(f"artifact_{node_id}{ext}").write_text(content, encoding="utf-8")
        return True

@pytest.mark.asyncio
async def test_mini_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    nodes = [
        PlanNode(id="R1", title="R1", type="execute", suggested_agent_role="Researcher"),
        PlanNode(id="R2", title="R2", type="execute", suggested_agent_role="Researcher"),
        PlanNode(id="M1", title="M1", type="manage", suggested_agent_role=""),
        PlanNode(id="W1", title="W1", type="execute", suggested_agent_role="", deps=["R1", "R2", "M1"]),
    ]
    dag = TaskGraph(nodes)

    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="contenu", provider="p", model_used="m")
    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)
    async def fake_run_manager(subplan):
        from core.agents.schemas import ManagerOutput, ManagerAssignment
        return ManagerOutput(
            assignments=[ManagerAssignment(node_id="W1", agent_role="Writer_FR")],
            quality_checks=["qc"],
        )
    monkeypatch.setattr(orch_exec, "run_manager", fake_run_manager)

    order = []
    async def on_end(node, node_id, status):
        order.append(node_id)

    res1 = await run_graph(dag, DummyStorage(), "run1", on_node_end=on_end)
    assert res1["status"] == "success"
    assert set(order[:2]) == {"R1","R2"}
    assert order[-1] == "W1"
    assert dag.nodes["W1"].suggested_agent_role == "Writer_FR"
    for nid in ["R1","R2","W1"]:
        assert Path(f"artifact_{nid}.md").exists()
        side = json.loads(Path(f"artifact_{nid}.llm.json").read_text())
        assert side["provider"] == "p" and side["model_used"] == "m"

    await run_graph(dag, DummyStorage(), "run1")
    summary = json.loads(Path(".runs/run1/summary.json").read_text())
    assert summary["skipped_count"] == 4
