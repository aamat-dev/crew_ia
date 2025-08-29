import pytest

@pytest.mark.asyncio
async def test_list_nodes_for_run(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/nodes?order_by=key")
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 3
    assert all("status" in n for n in js["items"])


@pytest.mark.asyncio
async def test_nodes_ordering(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/nodes?order_by=created_at&order_dir=asc")
    items = r.json()["items"]
    dates = [it["created_at"] for it in items]
    assert dates == sorted(dates)

    r = await client.get(f"/runs/{run_id}/nodes?order_by=-created_at")
    items = r.json()["items"]
    dates = [it["created_at"] for it in items]
    assert dates == sorted(dates, reverse=True)

    r = await client.get(f"/runs/{run_id}/nodes?order_by=foo")
    assert r.status_code == 422

    r = await client.get(
        f"/runs/{run_id}/nodes?status=completed&order_by=created_at&order_dir=asc&offset=1"
    )
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["key"] == "n2"
