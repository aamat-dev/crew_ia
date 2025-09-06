import uuid
import datetime as dt

import pytest
from sqlalchemy.dialects.postgresql import insert

from backend.api.fastapi_app.models.agent import Agent, AgentModelsMatrix


@pytest.mark.asyncio
async def test_get_agents_link_header(client):
    for i in range(2):
        payload = {"name": f"A{i}", "role": "manager", "domain": "frontend"}
        await client.post(
            "/agents", json=payload, headers={"X-Request-ID": f"r{i}"}
        )
    r = await client.get("/agents", params={"limit": 1})
    assert r.status_code == 200
    assert "Link" in r.headers


@pytest.mark.asyncio
async def test_post_agent_conflict(client):
    payload = {"name": "dup", "role": "manager", "domain": "frontend"}
    r1 = await client.post("/agents", json=payload, headers={"X-Request-ID": "r1"})
    assert r1.status_code == 201
    r2 = await client.post("/agents", json=payload, headers={"X-Request-ID": "r2"})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_patch_agent_version(client):
    payload = {"name": "upd", "role": "manager", "domain": "frontend"}
    r1 = await client.post("/agents", json=payload, headers={"X-Request-ID": "r1"})
    agent = r1.json()
    r2 = await client.patch(
        f"/agents/{agent['id']}",
        json={"prompt_user": "x"},
        headers={"X-Request-ID": "r2"},
    )
    assert r2.status_code == 200
    assert r2.json()["version"] == agent["version"] + 1


@pytest.mark.asyncio
async def test_deactivate_agent(client):
    payload = {"name": "inactive", "role": "manager", "domain": "frontend"}
    r1 = await client.post("/agents", json=payload, headers={"X-Request-ID": "r1"})
    agent_id = r1.json()["id"]
    r2 = await client.post(
        f"/agents/{agent_id}/deactivate", headers={"X-Request-ID": "r2"}
    )
    assert r2.status_code == 204
    r3 = await client.get("/agents", params={"is_active": False})
    ids = [a["id"] for a in r3.json()["items"]]
    assert agent_id in ids


@pytest.mark.asyncio
async def test_models_matrix_endpoint(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    rows = [
        {
            "id": uuid.uuid4(),
            "role": "manager",
            "domain": "frontend",
            "models": {"a": 1},
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": uuid.uuid4(),
            "role": "manager",
            "domain": "backend",
            "models": {"b": 2},
            "created_at": now,
            "updated_at": now,
        },
    ]
    await db_session.execute(insert(AgentModelsMatrix), rows)
    await db_session.commit()
    r = await client.get(
        "/agents/models-matrix", params={"role": "manager", "limit": 1}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["items"][0]["role"] == "manager"
    assert "Link" in r.headers
    assert "_links" in body
