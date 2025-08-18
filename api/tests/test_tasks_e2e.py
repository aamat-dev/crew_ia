import asyncio
import pytest


@pytest.mark.asyncio
async def test_create_and_follow_task(client):
    payload = {
        "title": "Adhoc run",
        "task_spec": {"type": "demo"},
        "options": {},
    }
    r = await client.post("/tasks", json=payload, headers={"X-API-Key": "test-key"})
    assert r.status_code == 202
    body = r.json()
    run_id = body["run_id"]
    assert body["status"] == "accepted"
    assert body["location"] == f"/runs/{run_id}"

    # Wait for completion
    for _ in range(20):
        r_run = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
        if r_run.status_code == 200 and r_run.json()["status"] == "completed":
            break
        await asyncio.sleep(0.1)
    assert r_run.json()["status"] == "completed"

    r_nodes = await client.get(f"/runs/{run_id}/nodes", headers={"X-API-Key": "test-key"})
    assert r_nodes.status_code == 200
    assert r_nodes.json()["total"] >= 1

    node_id = r_nodes.json()["items"][0]["id"]
    r_artifacts = await client.get(
        f"/nodes/{node_id}/artifacts", headers={"X-API-Key": "test-key"}
    )
    assert r_artifacts.status_code == 200
    assert r_artifacts.json()["total"] >= 1

    r_events = await client.get(f"/runs/{run_id}/events", headers={"X-API-Key": "test-key"})
    levels = [e["level"] for e in r_events.json()["items"]]
    assert "RUN_STARTED" in levels
    assert "RUN_COMPLETED" in levels


@pytest.mark.asyncio
async def test_create_task_requires_auth(client_noauth):
    payload = {"title": "x", "task_spec": {"type": "demo"}}
    r = await client_noauth.post("/tasks", json=payload)
    assert r.status_code == 401
