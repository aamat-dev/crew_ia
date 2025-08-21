import asyncio
import os
import pytest

from apps.orchestrator.executor import run_graph
from core.storage.file_adapter import FileStatusStore

# --------- DAG factice A -> B -> C -----------
class Node:
    def __init__(self, nid, role="Worker"):
        self.id = nid
        self.deps = []
        self.succ = []
        self.type = "execute"
        self.suggested_agent_role = role
        self.acceptance = []
        self.risks = []
        self.assumptions = []
        self.notes = []

class DummyDag:
    def __init__(self):
        self.nodes = {k: Node(k) for k in ["A", "B", "C"]}
        self.nodes["B"].deps = ["A"]
        self.nodes["C"].deps = ["B"]
        self.nodes["A"].succ = [self.nodes["B"]]
        self.nodes["B"].succ = [self.nodes["C"]]
        self.nodes["C"].succ = []

    def roots(self):
        return [self.nodes["A"]]

# --------------------------------------------

@pytest.mark.asyncio
async def test_recovery_resume(tmp_path, monkeypatch):
    # Forcer les dossiers de run dans tmp
    runs_root = tmp_path / ".runs"
    os.environ["RUNS_ROOT"] = str(runs_root)
    os.environ["NODE_RETRIES"] = "0"          # pour le premier run: pas de retry
    os.environ["RETRY_BASE_DELAY"] = "0.01"
    os.environ["MAX_CONCURRENCY"] = "2"

    dag = DummyDag()
    run_id = "run-reco-1"

    # Flag pour simuler l'échec la 1ère fois sur B
    flag_file = tmp_path / "flag.txt"
    flag_file.write_text("first")

    # Monkeypatch du worker LLM
    async def fake_agent_runner(node, storage):
        await asyncio.sleep(0.01)
        if node.id == "B":
            if flag_file.read_text().strip() == "first":
                flag_file.write_text("second")
                raise RuntimeError("Simulated crash on first pass")
        return "ok"

    import apps.orchestrator.executor as ex_mod
    monkeypatch.setattr(ex_mod, "agent_runner", fake_agent_runner)

    class DummyStorage:
        async def save_artifact(self, *args, **kwargs):
            return True
    storage = DummyStorage()

    # 1) Premier run: A completed, B failed, C déclenche une erreur de dépendance
    with pytest.raises(RuntimeError):
        await run_graph(dag, storage, run_id=run_id)
    st = FileStatusStore(runs_root=str(runs_root))
    assert st.read(run_id, "A").status == "completed"
    assert st.read(run_id, "B").status == "failed"
    assert st.read(run_id, "C") is None

    # 2) Second run: on autorise 1 retry, reprise avec même run_id
    os.environ["NODE_RETRIES"] = "1"
    res2 = await run_graph(dag, storage, run_id=run_id)
    assert res2["status"] == "success"
    assert st.read(run_id, "A").status == "completed"   # resté completed (skippé)
    assert st.read(run_id, "B").status == "completed"   # rejoué puis OK
    assert st.read(run_id, "C").status == "completed"   # OK
