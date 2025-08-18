import pytest

@pytest.mark.asyncio
async def test_list_runs(client, seed_sample):
    r = await client.get("/runs")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["title"] == "Sample Run" for item in data["items"])

@pytest.mark.asyncio
async def test_get_run_detail(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["nodes_total"] == 3
    assert body["summary"]["artifacts_total"] == 2
    assert body["summary"]["events_total"] == 2


@pytest.mark.asyncio
async def test_title_filter(client, seed_sample):
    r = await client.get("/runs?title_contains=sample")
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.get("/runs?title_contains=nomatch")
    assert r.status_code == 200
    assert r.json()["total"] == 0

@pytest.mark.asyncio
async def test_auth_required(client_noauth):
    r = await client_noauth.get("/runs")
    assert r.status_code == 401