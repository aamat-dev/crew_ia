import pytest

@pytest.mark.asyncio
async def test_list_nodes_for_run(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/nodes?order_by=key")
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 3
    assert all("status" in n for n in js["items"])