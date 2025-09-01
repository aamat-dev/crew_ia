import pytest


@pytest.mark.asyncio
async def test_create_task_201(client):
    r = await client.post(
        "/tasks",
        json={"title": "T1", "description": "desc"},
        headers={"X-API-Key": "test", "X-Request-ID": "req-1"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "T1"
    assert body["status"] == "draft"
    assert r.headers.get("X-Request-ID") == "req-1"
    assert r.headers.get("Location").startswith("/tasks/")


@pytest.mark.asyncio
async def test_create_task_whitespace_422(client):
    r = await client.post("/tasks", json={"title": "   "}, headers={"X-API-Key": "test"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_task_conflict_409(client):
    h = {"X-API-Key": "test"}
    r1 = await client.post("/tasks", json={"title": "T2"}, headers=h)
    assert r1.status_code == 201
    r2 = await client.post("/tasks", json={"title": " t2 "}, headers=h)
    assert r2.status_code == 409
