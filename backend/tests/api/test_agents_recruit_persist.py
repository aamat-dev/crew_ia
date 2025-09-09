import pytest


@pytest.mark.asyncio
async def test_recruit_persists_agent_in_db(client):
    payload = {
        "role_description": "Rédacteur/Traducteur",
        "role": "executor",
        "domain": "writer-translator",
    }

    r = await client.post(
        "/agents/recruit",
        json=payload,
        headers={"X-Request-ID": "req-recruit-1"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    agent_id = body.get("agent_id")
    assert agent_id, body

    # Vérifie qu'il apparaît dans le listing
    r2 = await client.get(
        "/agents",
        params={"role": "executor", "domain": "writer-translator", "is_active": True, "limit": 50},
    )
    assert r2.status_code == 200, r2.text
    items = r2.json().get("items", [])
    ids = {item.get("id") for item in items}
    assert agent_id in ids


@pytest.mark.asyncio
async def test_create_agent_conflict_returns_409(client):
    agent = {
        "name": "dup-agent-1",
        "role": "executor",
        "domain": "writer-translator",
        # on laisse les champs optionnels par défaut
    }

    r1 = await client.post(
        "/agents",
        json=agent,
        headers={"X-Request-ID": "req-a-1"},
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/agents",
        json=agent,
        headers={"X-Request-ID": "req-a-2"},
    )
    assert r2.status_code == 409, r2.text

