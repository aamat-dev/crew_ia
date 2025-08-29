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
async def test_list_events_filter_request_id(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get("/events", params={"run_id": run_id, "request_id": "req-1"})
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    assert js["items"][0]["request_id"] == "req-1"


@pytest.mark.asyncio
async def test_events_old_and_new_routes(client, seed_sample):
    run_id = seed_sample["run_id"]
    r1 = await client.get("/events", params={"run_id": run_id})
    r2 = await client.get(f"/runs/{run_id}/events")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_events_ordering(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/events?run_id={run_id}&order_by=timestamp&order_dir=asc")
    items = r.json()["items"]
    ts = [it["timestamp"] for it in items]
    assert ts == sorted(ts)

    r = await client.get(f"/events?run_id={run_id}&order_by=-timestamp")
    items = r.json()["items"]
    ts = [it["timestamp"] for it in items]
    assert ts == sorted(ts, reverse=True)

    r = await client.get(f"/events?run_id={run_id}&order_by=foo")
    assert r.status_code == 422

    r = await client.get(
        f"/events?run_id={run_id}&order_by=timestamp&order_dir=asc&offset=1"
    )
    items = r.json()["items"]
    assert len(items) == 1
