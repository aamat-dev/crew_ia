import pytest


@pytest.mark.asyncio
async def test_get_and_reactivate_agent(client):
    # 1) Créer un agent
    payload = {"name": "a1", "role": "manager", "domain": "front"}
    r_create = await client.post("/agents", json=payload, headers={"X-Request-ID": "r1"})
    assert r_create.status_code == 201
    agent = r_create.json()
    agent_id = agent["id"]

    # 2) GET /agents/{id}
    r_get = await client.get(f"/agents/{agent_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == agent_id

    # 3) Désactiver puis réactiver
    r_deact = await client.post(f"/agents/{agent_id}/deactivate", headers={"X-Request-ID": "r2"})
    assert r_deact.status_code == 204
    r_react = await client.post(f"/agents/{agent_id}/reactivate", headers={"X-Request-ID": "r3"})
    assert r_react.status_code == 204

    # 4) Vérifier qu'il est bien visible en actif
    r_list = await client.get("/agents", params={"is_active": True})
    assert r_list.status_code == 200
    items = r_list.json().get("items") or []
    assert any(it["id"] == agent_id for it in items)

