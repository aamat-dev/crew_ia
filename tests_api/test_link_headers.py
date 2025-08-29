import pytest


@pytest.mark.asyncio
async def test_nodes_link_headers(client, seed_sample):
    run_id = seed_sample["run_id"]
    # page 1
    r1 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1})
    assert r1.status_code == 200
    total = r1.json()["total"]
    assert r1.headers["X-Total-Count"] == str(total)
    link1 = r1.headers["Link"]
    assert 'rel="prev"' not in link1
    assert 'rel="next"' in link1 and 'offset=1' in link1

    # middle page
    r2 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1, "offset": 1})
    link2 = r2.headers["Link"]
    assert 'rel="prev"' in link2 and 'rel="next"' in link2
    assert 'offset=0' in link2 and 'offset=2' in link2

    # last page
    r3 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1, "offset": 2})
    link3 = r3.headers["Link"]
    assert 'rel="next"' not in link3
    assert 'rel="prev"' in link3 and 'offset=1' in link3


@pytest.mark.asyncio
async def test_nodes_links_preserve_filters(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(
        f"/runs/{run_id}/nodes",
        params={"limit": 1, "status": "completed", "order_by": "key"},
    )
    link = r.headers["Link"]
    assert "status=completed" in link
    assert "order_by=key" in link
