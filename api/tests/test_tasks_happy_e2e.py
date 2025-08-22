import pytest


@pytest.mark.asyncio
async def test_post_tasks_returns_run_id_and_location(async_client):
    payload = {
        "title": "Demo",
        "task": {"title": "Demo", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-123"}
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    body = r.json()
    run_id = body["run_id"]
    assert body["location"] == f"/runs/{run_id}"


@pytest.mark.asyncio
async def test_post_tasks_requires_api_key(client_noauth):
    payload = {"title": "x", "task": {"plan": [{"id": "n1", "title": "T1"}]}}
    r = await client_noauth.post("/tasks", json=payload)
    assert r.status_code == 401
