import pytest
from ..conftest import wait_status


@pytest.mark.asyncio
async def test_create_and_follow_task(client):
    r = await client.post(
        "/tasks",
        json={"title": "Adhoc run", "task_spec": {"type": "demo"}},
        headers={"X-API-Key": "test-key"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "accepted"
    run_id = body["run_id"]

    assert await wait_status(client, run_id, "completed", timeout=5.0)
    r_status = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
    assert r_status.status_code == 200
    assert r_status.json()["status"] == "completed"

    r_events = await client.get(
        f"/events", params={"run_id": run_id}, headers={"X-API-Key": "test-key"}

    )
    assert r_events.status_code == 200
    assert r_events.json()["total"] >= 1

    r_nodes = await client.get(f"/runs/{run_id}/nodes", headers={"X-API-Key": "test-key"})
    assert r_nodes.status_code == 200
    assert r_nodes.json()["total"] == 1


@pytest.mark.asyncio
async def test_create_task_requires_auth(client_noauth):
    r = await client_noauth.post(
        "/tasks", json={"title": "x", "task_spec": {"type": "demo"}}
    )
    assert r.status_code == 401
