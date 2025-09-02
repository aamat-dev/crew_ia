import pytest
from api.fastapi_app import deps


@pytest.mark.asyncio
async def test_viewer_forbidden_on_post(client, monkeypatch):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    r = await client.post(
        "/agents",
        json={"name": "r1", "role": "manager", "domain": "front"},
        headers={"X-Role": "viewer", "X-Request-ID": "r1"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_editor_allowed(client, monkeypatch):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    r = await client.post(
        "/agents",
        json={"name": "r2", "role": "manager", "domain": "front"},
        headers={"X-Role": "editor", "X-Request-ID": "r2"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_no_rbac_header_required_when_flag_off(client, monkeypatch):
    monkeypatch.setattr(deps, "FEATURE_RBAC", False)
    r = await client.post(
        "/agents",
        json={"name": "r3", "role": "manager", "domain": "front"},
        headers={"X-Request-ID": "r3"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_get_allowed_without_role_header(client, monkeypatch):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    r = await client.get("/agents")
    assert r.status_code == 200
