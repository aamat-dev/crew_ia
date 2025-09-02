import pytest

@pytest.mark.asyncio
async def test_runs_pagination(client, seed_sample):
    r = await client.get("/runs")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert "_links" in body

    total = body["total"]

    r2 = await client.get("/runs?limit=500&offset=5")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 200
    assert body2["offset"] == 5

    r3 = await client.get("/runs?offset=-1")
    assert r3.status_code == 422

    r4 = await client.get("/runs?limit=50")
    assert r4.status_code == 200
    assert r4.json()["limit"] == 50

    r5 = await client.get("/runs?limit=0")
    assert r5.status_code == 422

    r6 = await client.get(f"/runs?offset={total + 10}")
    assert r6.status_code == 200
    body6 = r6.json()
    assert body6["items"] == []
    assert body6["total"] == total

@pytest.mark.asyncio
async def test_nodes_pagination(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/nodes")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert "_links" in body

    r2 = await client.get(f"/runs/{run_id}/nodes?limit=500")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 200

    r3 = await client.get(f"/runs/{run_id}/nodes?offset=-1")
    assert r3.status_code == 422

    r4 = await client.get(f"/runs/{run_id}/nodes?limit=50")
    assert r4.status_code == 200
    assert r4.json()["limit"] == 50

    r5 = await client.get(f"/runs/{run_id}/nodes?limit=0")
    assert r5.status_code == 422

@pytest.mark.asyncio
async def test_artifacts_pagination(client, seed_sample):
    node_id = seed_sample["node_ids"][0]
    r = await client.get(f"/nodes/{node_id}/artifacts")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert "_links" in body

    r2 = await client.get(f"/nodes/{node_id}/artifacts?limit=500")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 200

    r3 = await client.get(f"/nodes/{node_id}/artifacts?offset=-1")
    assert r3.status_code == 422

    r4 = await client.get(f"/nodes/{node_id}/artifacts?limit=50")
    assert r4.status_code == 200
    assert r4.json()["limit"] == 50

    r5 = await client.get(f"/nodes/{node_id}/artifacts?limit=0")
    assert r5.status_code == 422

    # filtre type inexistant -> total doit refléter les mêmes filtres
    r6 = await client.get(f"/nodes/{node_id}/artifacts?type=sidecar&limit=500")
    assert r6.status_code == 200
    body6 = r6.json()
    assert body6["limit"] == 200
    assert body6["total"] == 0
    assert body6["items"] == []

@pytest.mark.asyncio
async def test_events_pagination(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get("/events", params={"run_id": run_id})
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert "_links" in body

    r2 = await client.get("/events", params={"run_id": run_id, "limit": 500})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["limit"] == 200

    r3 = await client.get("/events", params={"run_id": run_id, "offset": -1})
    assert r3.status_code == 422

    r4 = await client.get("/events", params={"run_id": run_id, "limit": 50})
    assert r4.status_code == 200
    assert r4.json()["limit"] == 50

    r5 = await client.get("/events", params={"run_id": run_id, "limit": 0})
    assert r5.status_code == 422


@pytest.mark.asyncio
async def test_runs_ordering_desc_started_at(client, seed_sample):
    r = await client.get("/runs?order_by=started_at&order_dir=desc&limit=50")
    assert r.status_code == 200
    items = r.json()["items"]
    if len(items) >= 2:
        assert items[0]["started_at"] >= items[1]["started_at"]
