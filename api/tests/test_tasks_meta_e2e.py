import asyncio
import json
import time

import pytest
import uuid
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event


@pytest.mark.asyncio
async def test_events_include_llm_metadata(async_client, monkeypatch, tmp_path, db_session):
    async def fake_run_graph(dag, storage, run_id, override_completed, dry_run, on_node_start, on_node_end):
        node = {"title": "T1"}
        node_key = "n1"
        await on_node_start(node, node_key)
        node_dir = tmp_path / run_id / "nodes" / node_key
        node_dir.mkdir(parents=True)
        meta = {
            "provider": "openai",
            "model": "gpt4",
            "latency_ms": 123,
            "usage": {"prompt_tokens": 1},
        }
        (node_dir / f"artifact_{node_key}.llm.json").write_text(json.dumps(meta))
        await on_node_end(node, node_key, "completed")
        return {"status": "success"}

    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setattr("apps.orchestrator.api_runner.run_graph", fake_run_graph)

    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-456"}
    payload = {
        "title": "Meta",
        "task": {"title": "Meta", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    run_id = r.json()["run_id"]
    run_uuid = uuid.UUID(run_id)

    deadline = time.monotonic() + 10.0  # 10s max
    while time.monotonic() < deadline:
        rs = await async_client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
        if rs.json().get("status") in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)

    events = await async_client.get(
        "/events", params={"run_id": run_id}, headers={"X-API-Key": "test-key"}
    )
    assert events.status_code == 200
    node_events = [e for e in events.json()["items"] if e["level"] == "NODE_COMPLETED"]
    assert node_events, "missing NODE_COMPLETED"

    meta = json.loads(node_events[0]["message"])
    assert meta.get("provider") == "openai"
    assert meta.get("model") == "gpt4"
    assert meta.get("latency_ms") == 123
    assert meta.get("usage") == {"prompt_tokens": 1, "completion_tokens": 0}
    assert meta.get("request_id") == "req-456"

    # nettoyage des données créées pendant le test
    await db_session.execute(delete(Event).where(Event.run_id == run_uuid))
    await db_session.execute(
        delete(Artifact).where(
            Artifact.node_id.in_(select(Node.id).where(Node.run_id == run_uuid))
        )
    )
    await db_session.execute(delete(Node).where(Node.run_id == run_uuid))
    await db_session.execute(delete(Run).where(Run.id == run_uuid))
    await db_session.commit()
