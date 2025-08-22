import pytest

@pytest.mark.asyncio
async def test_list_events_filter_level(client, seed_sample):
    run_id = seed_sample["run_id"]

    r = await client.get("/events", params={"run_id": run_id, "level": "ERROR"})

    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    assert js["items"][0]["level"] == "ERROR"


@pytest.mark.asyncio
async def test_list_events_filter_q(client, seed_sample):
    run_id = seed_sample["run_id"]

    r = await client.get("/events", params={"run_id": run_id, "q": "boom"})
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    assert js["items"][0]["message"] == "boom"


@pytest.mark.asyncio
async def test_events_old_and_new_routes(client, seed_sample):
    run_id = seed_sample["run_id"]
    r1 = await client.get("/events", params={"run_id": run_id})
    r2 = await client.get(f"/runs/{run_id}/events")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
