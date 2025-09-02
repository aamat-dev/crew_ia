import json
import uuid
from pathlib import Path

import pytest

from core.planning.task_graph import PlanNode, TaskGraph
import apps.orchestrator.executor as exec_mod


class DummyStorage:
    def __init__(self):
        self.feedbacks = []
        self.events = []

    async def save_run(self, *a, **k):
        pass

    async def save_node(self, *a, **k):
        pass

    async def save_artifact(self, *a, **k):
        pass

    async def save_feedback(self, **k):
        self.feedbacks.append(k)

    async def save_event(self, **k):
        self.events.append(k)


@pytest.mark.asyncio
async def test_autoreview_creates_feedback_and_event(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def fake_execute(node, *a, **k):
        return {"markdown": "ok", "llm": {}}

    async def fake_review(content):
        return {"score": 40, "comment": "bad", "llm": {"provider": "p", "model_used": "m"}}

    monkeypatch.setattr(exec_mod, "_execute_node", fake_execute)
    monkeypatch.setattr(exec_mod, "_invoke_auto_reviewer", fake_review)
    monkeypatch.setenv("FEEDBACK_CRITICAL_THRESHOLD", "60")

    node = PlanNode(id="n1", title="N1", type="execute", suggested_agent_role="Researcher")
    node.db_id = str(uuid.uuid4())
    dag = TaskGraph([node])
    storage = DummyStorage()

    run_id = str(uuid.uuid4())
    await exec_mod.run_graph(dag, storage, run_id)

    assert storage.feedbacks, "feedback should be saved"
    fb = storage.feedbacks[0]
    assert fb["source"] == "auto" and fb["score"] == 40

    sidecar = Path(f".runs/{run_id}/nodes/n1/n1.review.llm.json")
    assert sidecar.exists()
    data = json.loads(sidecar.read_text())
    assert data.get("model") == "m"

    assert storage.events, "critical event should be emitted"
    assert storage.events[0]["message"] == "feedback.critical"

