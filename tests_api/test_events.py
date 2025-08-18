import pytest

@pytest.mark.asyncio
async def test_list_events_filter_level(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/events?level=ERROR")
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    assert js["items"][0]["level"] == "ERROR"


@pytest.mark.asyncio
async def test_list_events_filter_q(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/events?q=boom")
    assert r.status_code == 200
    js = r.json()
    assert js["total"] == 1
    assert js["items"][0]["message"] == "boom"