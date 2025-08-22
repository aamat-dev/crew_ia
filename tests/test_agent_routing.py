from pathlib import Path
import pytest

from apps.orchestrator.executor import _execute_node
from core.planning.task_graph import PlanNode, TaskGraph
from core.llm.providers.base import LLMResponse
import core.agents.executor_llm as exec_mod


@pytest.mark.asyncio
async def test_agent_routing_writer(monkeypatch, tmp_path):
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="texte", provider="p", model_used="m")

    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("RUNS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    class DummyStorage:
        def __init__(self):
            self.calls = []

        async def save_artifact(self, node_id, content, *, ext):
            self.calls.append((str(node_id), ext, content))

    node = PlanNode(id="w1", title="Titre", type="execute", suggested_agent_role="Writer_FR")
    setattr(node, "db_id", "11111111-1111-1111-1111-111111111111")
    dag = TaskGraph([node])
    storage = DummyStorage()
    res = await _execute_node(node, storage, dag, run_id="r1", node_key="w1")

    content = res["markdown"]
    assert content.startswith("# ")
    side = res["llm"]
    assert side["provider"] == "p"
    assert side["model"] == "m"
    assert set(side["prompts"].keys()) == {"system", "user", "final"}

    # Vérifie la persistance FS
    md_path = Path(tmp_path, "r1", "nodes", "w1", "artifact_w1.md")
    side_path = Path(tmp_path, "r1", "nodes", "w1", "artifact_w1.llm.json")
    assert md_path.exists()
    assert side_path.exists()

    # Vérifie les appels storage avec node_id
    assert storage.calls[0][0] == "11111111-1111-1111-1111-111111111111"
    assert storage.calls[1][0] == "11111111-1111-1111-1111-111111111111"
    assert storage.calls[0][1] == ".md"
    assert storage.calls[1][1] == ".llm.json"


@pytest.mark.asyncio
async def test_agent_routing_skip_db_without_uuid(monkeypatch, tmp_path):
    async def fake_run_llm(req, primary=None, fallback_order=None):
        return LLMResponse(text="texte", provider="p", model_used="m")

    monkeypatch.setattr(exec_mod, "run_llm", fake_run_llm)
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("RUNS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    class DummyStorage:
        def __init__(self):
            self.calls = []

        async def save_artifact(self, node_id, content, *, ext):
            self.calls.append((str(node_id), ext))

    node = PlanNode(id="w2", title="Titre", type="execute", suggested_agent_role="Writer_FR")
    dag = TaskGraph([node])
    storage = DummyStorage()
    await _execute_node(node, storage, dag, run_id="r2", node_key="w2")

    md_path = Path(tmp_path, "r2", "nodes", "w2", "artifact_w2.md")
    side_path = Path(tmp_path, "r2", "nodes", "w2", "artifact_w2.llm.json")
    assert md_path.exists()
    assert side_path.exists()
    assert storage.calls == []
