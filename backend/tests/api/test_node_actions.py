import uuid

import pytest
from fastapi import HTTPException

from backend.orchestrator import orchestrator_adapter


@pytest.mark.asyncio
async def test_patch_node_pause(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        assert node_id_arg == node_id
        assert action == "pause"
        assert payload == {}
        return {"status_after": "paused"}

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(f"/nodes/{node_id}", json={"action": "pause"})
    assert r.status_code == 200
    assert r.json() == {"node_id": str(node_id), "status_after": "paused"}


@pytest.mark.asyncio
async def test_patch_node_resume(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        assert action == "resume"
        return {"status_after": "running"}

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(f"/nodes/{node_id}", json={"action": "resume"})
    assert r.status_code == 200
    assert r.json() == {"node_id": str(node_id), "status_after": "running"}


@pytest.mark.asyncio
async def test_patch_node_override(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        assert action == "override"
        assert payload["prompt"] == "recalc"
        return {"status_after": "queued", "sidecar_updated": True}

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(
        f"/nodes/{node_id}",
        json={"action": "override", "prompt": "recalc"},
    )
    assert r.status_code == 200
    assert r.json() == {
        "node_id": str(node_id),
        "status_after": "queued",
        "sidecar_updated": True,
    }


@pytest.mark.asyncio
async def test_patch_node_skip(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        assert action == "skip"
        return {"status_after": "skipped"}

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(f"/nodes/{node_id}", json={"action": "skip"})
    assert r.status_code == 200
    assert r.json() == {"node_id": str(node_id), "status_after": "skipped"}


@pytest.mark.asyncio
async def test_patch_node_unknown_action(client):
    node_id = uuid.uuid4()
    r = await client.patch(f"/nodes/{node_id}", json={"action": "foo"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_node_not_found(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        raise HTTPException(status_code=404, detail="node not found")

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(f"/nodes/{node_id}", json={"action": "pause"})
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_patch_node_conflict(client, monkeypatch):
    node_id = uuid.uuid4()

    async def fake_action(node_id_arg, action, payload):
        raise HTTPException(status_code=409, detail="conflict")

    monkeypatch.setattr(orchestrator_adapter, "node_action", fake_action)
    r = await client.patch(f"/nodes/{node_id}", json={"action": "pause"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_patch_node_resume_invalid_state(client):
    node_id = uuid.uuid4()
    # Par défaut l'état est "running", resume doit donc échouer
    r = await client.patch(f"/nodes/{node_id}", json={"action": "resume"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_patch_node_pause_twice_conflict(client):
    node_id = uuid.uuid4()
    r1 = await client.patch(f"/nodes/{node_id}", json={"action": "pause"})
    assert r1.status_code == 200
    r2 = await client.patch(f"/nodes/{node_id}", json={"action": "pause"})
    assert r2.status_code == 409
