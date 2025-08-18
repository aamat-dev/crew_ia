import asyncio
import pytest


@pytest.mark.asyncio
async def test_create_and_follow_task(client):
    r = await client.post(
        "/tasks",
        json={"title": "Adhoc run", "params": {"foo": "bar"}},
        headers={"X-API-Key": "test-key"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "accepted"
    run_id = body["run_id"]

    await asyncio.sleep(0.3)

    r_status = await client.get(f"/tasks/{run_id}", headers={"X-API-Key": "test-key"})
    assert r_status.status_code == 200
    assert r_status.json()["status"] == "completed"

    r_run = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
    assert r_run.status_code == 200
    assert r_run.json()["status"] == "completed"

    r_events = await client.get(f"/runs/{run_id}/events", headers={"X-API-Key": "test-key"})
    assert r_events.status_code == 200
    assert r_events.json()["total"] == 1

    r_nodes = await client.get(f"/runs/{run_id}/nodes", headers={"X-API-Key": "test-key"})
    assert r_nodes.status_code == 200
    assert r_nodes.json()["total"] == 1


@pytest.mark.asyncio
async def test_create_task_requires_auth(client_noauth):
    r = await client_noauth.post("/tasks", json={"title": "x"})
    assert r.status_code == 401
