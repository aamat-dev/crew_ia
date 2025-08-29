import pytest
import datetime as dt
import uuid
from sqlalchemy import insert, delete
from api.database.models import Run

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
async def test_get_run_summary_ok(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["nodes_total"] == 3
    assert body["nodes_completed"] == 2
    assert body["nodes_failed"] == 1
    assert body["artifacts_total"] == 2
    assert body["events_total"] == 2
    assert body["duration_ms"] == 300000


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


@pytest.mark.asyncio
async def test_runs_ordering(client, db_session, seed_sample):
    now = dt.datetime.now(dt.timezone.utc)
    run1 = {
        "id": uuid.uuid4(),
        "title": "Run1",
        "status": "completed",
        "started_at": now - dt.timedelta(minutes=10),
        "ended_at": now - dt.timedelta(minutes=9),
    }
    run2 = {
        "id": uuid.uuid4(),
        "title": "Run2",
        "status": "completed",
        "started_at": now - dt.timedelta(minutes=1),
        "ended_at": now,
    }
    await db_session.execute(insert(Run), [run1, run2])
    await db_session.commit()
    try:
        r = await client.get("/runs?order_by=started_at&order_dir=asc")
        times = [it["started_at"] for it in r.json()["items"][:3]]
        assert times == sorted(times)

        r = await client.get("/runs?order_by=-started_at")
        times_desc = [it["started_at"] for it in r.json()["items"][:3]]
        assert times_desc == sorted(times_desc, reverse=True)

        r = await client.get("/runs?order_by=foo")
        assert r.status_code == 422

        r = await client.get(
            "/runs?status=completed&order_by=started_at&order_dir=desc&offset=1&limit=1"
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["started_at"] == times_desc[1]
    finally:
        await db_session.execute(delete(Run).where(Run.id.in_([run1["id"], run2["id"]])))
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_run_summary_404(client):
    r = await client.get(f"/runs/{uuid.uuid4()}/summary")
    assert r.status_code == 404
