import pytest
import uuid


@pytest.mark.asyncio
async def test_invalid_task_spec_returns_400(async_client):
    payload = {"title": "X", "task_spec": {"plan": "not a list"}}
    r = await async_client.post("/tasks", headers={"X-API-Key": "test-key"}, json=payload)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_rate_limit_returns_429(async_client, monkeypatch):
    async def fake_schedule_run(**kwargs):
        return uuid.uuid4()

    monkeypatch.setattr(
        "backend.api.fastapi_app.routes.tasks.schedule_run", fake_schedule_run
    )

    payload = {"title": "R", "task_spec": {"type": "demo"}}
    headers = {"X-API-Key": "test-key"}
    for _ in range(3):
        res = await async_client.post("/tasks", headers=headers, json=payload)
        assert res.status_code == 202
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 429
