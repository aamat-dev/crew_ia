import pytest
import uuid


@pytest.mark.asyncio
async def test_create_task_201(client):
    title = f"T1-{uuid.uuid4()}"
    r = await client.post(
        "/tasks",
        json={"title": title, "description": "desc"},
        headers={"X-API-Key": "test", "X-Request-ID": "req-1"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == title
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
    base = f"T2-{uuid.uuid4()}"
    r1 = await client.post("/tasks", json={"title": base}, headers=h)
    assert r1.status_code == 201
    r2 = await client.post("/tasks", json={"title": f" {base.lower()} "}, headers=h)
    assert r2.status_code == 409
