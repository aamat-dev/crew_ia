import asyncio
import json
import pytest

@pytest.mark.asyncio
async def test_events_include_llm_metadata(client):
    payload = {
        "title": "LLMMeta",
        "task": {"title": "LLMMeta", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []}
    }
    r = await client.post("/tasks", json=payload, headers={"X-API-Key": "test-key"})
    assert r.status_code == 202
    rid = r.json()["run_id"]

    # poll
    for _ in range(60):
        rr = await client.get(f"/runs/{rid}", headers={"X-API-Key": "test-key"})
        if rr.json()["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)

    ev = await client.get(
        "/events",
        params={"run_id": rid},
        headers={"X-API-Key": "test-key"},
    )
    assert ev.status_code == 200
    items = ev.json()["items"]
    node_completed = [e for e in items if e["level"] == "NODE_COMPLETED"]
    assert node_completed, "NODE_COMPLETED event missing"
    # payload est dans e["message"] (JSON string)
    msg = json.loads(node_completed[0]["message"])
    assert isinstance(msg, dict)
