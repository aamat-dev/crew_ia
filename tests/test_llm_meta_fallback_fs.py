import json
import uuid
from types import SimpleNamespace

import pytest

from apps.orchestrator.api_runner import run_task
from core.events.publisher import EventPublisher
from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Node, Run


class DummyStorage:
    def __init__(self):
        self.events = []
        self.nodes = {}
        self.saved_run = None

    async def save_node(self, node: Node):
        self.nodes[node.key] = node
        return node

    async def get_node_id_by_logical(self, run_id: str, logical_id: str):
        node = self.nodes.get(logical_id)
        return str(node.id) if node else None

    async def list_artifacts_for_node(self, node_id: str):
        return []

    async def save_event(self, run_id, node_id, level, message):
        self.events.append(
            {"run_id": run_id, "node_id": node_id, "level": level, "message": message}
        )

    async def save_run(self, run: Run):
        self.saved_run = run


@pytest.mark.asyncio
async def test_llm_meta_fallback_fs(tmp_path, monkeypatch):
    storage_backend = DummyStorage()
    storage = CompositeAdapter([storage_backend])
    publisher = EventPublisher(storage)
    run_id = str(uuid.uuid4())

    async def fake_run_graph(
        dag, storage, run_id, override_completed, dry_run, on_node_start, on_node_end
    ):
        node = {"title": "T1"}
        node_key = "n1"
        await on_node_start(node, node_key)
        node_dir = tmp_path / run_id / "nodes" / node_key
        node_dir.mkdir(parents=True)
        meta = {
            "provider": "openai",
            "model_used": "gpt4",
            "latency_ms": 123,
            "usage": {"prompt_tokens": 1},
            "prompts": {"user": "hello"},
        }
        (node_dir / f"artifact_{node_key}.llm.json").write_text(json.dumps(meta))
        await on_node_end(node, node_key, "completed")
        return {"status": "success"}

    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setattr("apps.orchestrator.api_runner.run_graph", fake_run_graph)

    async def fast_sleep(_):
        return

    monkeypatch.setattr("apps.orchestrator.api_runner.anyio.sleep", fast_sleep)

    options = SimpleNamespace(override=[], dry_run=False)
    await run_task(
        run_id=run_id,
        task_spec={"plan": [{"id": "n1", "title": "T1"}], "type": "demo"},
        options=options,
        storage=storage,
        event_publisher=publisher,
        title="T1",
        request_id="req-1",
    )

    events = [
        json.loads(e["message"])
        for e in storage_backend.events
        if e["level"] == "NODE_COMPLETED"
    ]
    assert events, "NODE_COMPLETED manquant"
    payload = events[0]
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt4"
    assert payload["latency_ms"] == 123
    assert payload["usage"] == {"prompt_tokens": 1}
    assert payload["prompts"] == {"user": "hello"}
    assert payload["request_id"] == "req-1"
