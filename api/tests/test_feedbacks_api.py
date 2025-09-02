import uuid
import pytest

from api.fastapi_app import deps


@pytest.mark.asyncio
async def test_post_feedback_requires_request_id(monkeypatch, async_client, seed_sample):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    run_id = seed_sample["run_id"]
    node_id = seed_sample["node_ids"][0]
    payload = {
        "run_id": str(run_id),
        "node_id": str(node_id),
        "source": "human",
        "score": 10,
        "comment": "oops",
    }
    r = await async_client.post("/feedbacks", json=payload, headers={"X-Role": "editor"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_feedback_requires_role(monkeypatch, async_client, seed_sample):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    run_id = seed_sample["run_id"]
    node_id = seed_sample["node_ids"][0]
    payload = {
        "run_id": str(run_id),
        "node_id": str(node_id),
        "source": "human",
        "score": 20,
        "comment": "no role",
    }
    r = await async_client.post(
        "/feedbacks",
        json=payload,
        headers={"X-Role": "viewer", "X-Request-ID": "r1"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_feedback_ok(monkeypatch, async_client, seed_sample):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    run_id = seed_sample["run_id"]
    node_id = seed_sample["node_ids"][0]
    payload = {
        "run_id": str(run_id),
        "node_id": str(node_id),
        "source": "human",
        "score": 35,
        "comment": "Format JSON invalide",
        "metadata": {"path": "out.json"},
    }
    r = await async_client.post(
        "/feedbacks",
        json=payload,
        headers={"X-Role": "editor", "X-Request-ID": "demo-1"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["score"] == 35
    assert body["comment"] == "Format JSON invalide"


@pytest.mark.asyncio
async def test_list_feedbacks_filter(monkeypatch, async_client, seed_sample):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    run_id = seed_sample["run_id"]
    node1, node2 = seed_sample["node_ids"][:2]
    headers = {"X-Role": "editor", "X-Request-ID": "r1"}
    await async_client.post(
        "/feedbacks",
        json={
            "run_id": str(run_id),
            "node_id": str(node1),
            "source": "human",
            "score": 10,
            "comment": "a",
        },
        headers=headers,
    )
    await async_client.post(
        "/feedbacks",
        json={
            "run_id": str(run_id),
            "node_id": str(node2),
            "source": "auto",
            "score": 80,
            "comment": "b",
        },
        headers=headers,
    )
    r = await async_client.get(f"/feedbacks?node_id={node1}")
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    r2 = await async_client.get(f"/feedbacks?run_id={run_id}")
    assert r2.status_code == 200
    assert r2.json()["total"] >= 2


@pytest.mark.asyncio
async def test_get_nodes_includes_feedbacks(monkeypatch, async_client, seed_sample):
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    run_id = seed_sample["run_id"]
    node_id = seed_sample["node_ids"][0]
    headers = {"X-Role": "editor", "X-Request-ID": "rr1"}
    await async_client.post(
        "/feedbacks",
        json={
            "run_id": str(run_id),
            "node_id": str(node_id),
            "source": "human",
            "score": 50,
            "comment": "c",
        },
        headers=headers,
    )
    r = await async_client.get(f"/runs/{run_id}/nodes")
    assert r.status_code == 200
    items = r.json()["items"]
    target = [n for n in items if n["id"] == str(node_id)][0]
    assert len(target["feedbacks"]) == 1
    assert target["feedbacks"][0]["comment"] == "c"
