import asyncio
import pytest

@pytest.mark.asyncio
async def test_create_and_follow_task(client):
    payload = {
        "title": "Adhoc run",
        "task": { "title": "Mini plan", "plan": [ { "id": "n1", "title": "T1" } ] },
        "options": { "resume": False, "dry_run": False, "override": [] }
    }
    r = await client.post("/tasks", json=payload, headers={"X-API-Key": "test-key"})
    assert r.status_code == 202, r.text
    body = r.json()
    run_id = body["run_id"]
    assert body["status"] == "accepted"
    assert body["location"] == f"/runs/{run_id}"

    # Poll jusqu'à completion
    for _ in range(60):
        rr = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
        assert rr.status_code == 200
        if rr.json()["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)
    assert rr.json()["status"] == "completed"

    # Noeuds + artifacts
    r_nodes = await client.get(f"/runs/{run_id}/nodes", headers={"X-API-Key": "test-key"})
    assert r_nodes.status_code == 200
    items = r_nodes.json()["items"]
    assert len(items) >= 1
    node_id = items[0]["id"]

    r_artifacts = await client.get(f"/nodes/{node_id}/artifacts", headers={"X-API-Key": "test-key"})
    assert r_artifacts.status_code == 200
    assert r_artifacts.json()["total"] >= 1

    # Events
    r_events = await client.get(
        "/events",
        params={"run_id": run_id},
        headers={"X-API-Key": "test-key"},
    )
    levels = [e["level"] for e in r_events.json()["items"]]
    assert "RUN_STARTED" in levels
    assert "RUN_COMPLETED" in levels

@pytest.mark.asyncio
async def test_create_task_requires_auth(client_noauth):
    payload = { "title": "x", "task": { "plan": [ { "id": "n1", "title": "T1" } ] } }
    r = await client_noauth.post("/tasks", json=payload)
    assert r.status_code == 401
