import pytest
import uuid
import datetime as dt
from sqlalchemy import insert, delete

from api.database.models import Run, Artifact, Event


@pytest.mark.asyncio
async def test_runs_link_headers(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_ids = [uuid.uuid4() for _ in range(3)]
    await db_session.execute(
        insert(Run),
        [
            {
                "id": rid,
                "title": f"Run {i}",
                "status": "completed",
                "started_at": now,
                "ended_at": now,
            }
            for i, rid in enumerate(run_ids, start=1)
        ],
    )
    await db_session.commit()
    try:
        r1 = await client.get("/runs", params={"limit": 1})
        assert r1.status_code == 200
        total = r1.json()["total"]
        assert r1.headers["X-Total-Count"] == str(total)
        link1 = r1.headers["Link"]
        assert 'rel="prev"' not in link1
        assert 'rel="next"' in link1 and 'offset=1' in link1

        r2 = await client.get("/runs", params={"limit": 1, "offset": 1})
        link2 = r2.headers["Link"]
        assert 'rel="prev"' in link2 and 'offset=0' in link2
        assert 'rel="next"' in link2 and 'offset=2' in link2

        r3 = await client.get("/runs", params={"limit": 1, "offset": 2})
        link3 = r3.headers["Link"]
        assert 'rel="next"' not in link3
        assert 'rel="prev"' in link3 and 'offset=1' in link3
    finally:
        await db_session.execute(delete(Run).where(Run.id.in_(run_ids)))
        await db_session.commit()


@pytest.mark.asyncio
async def test_nodes_link_headers(client, seed_sample):
    run_id = seed_sample["run_id"]
    r1 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1})
    total = r1.json()["total"]
    assert r1.headers["X-Total-Count"] == str(total)
    link1 = r1.headers["Link"]
    assert 'rel="prev"' not in link1
    assert 'rel="next"' in link1 and 'offset=1' in link1

    r2 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1, "offset": 1})
    link2 = r2.headers["Link"]
    assert 'rel="prev"' in link2 and 'rel="next"' in link2
    assert 'offset=0' in link2 and 'offset=2' in link2

    r3 = await client.get(f"/runs/{run_id}/nodes", params={"limit": 1, "offset": 2})
    link3 = r3.headers["Link"]
    assert 'rel="next"' not in link3
    assert 'rel="prev"' in link3 and 'offset=1' in link3


@pytest.mark.asyncio
async def test_artifacts_link_headers(client, seed_sample, db_session):
    node_id = seed_sample["node_ids"][0]
    now = dt.datetime.now(dt.timezone.utc)
    await db_session.execute(
        insert(Artifact),
        [
            {
                "id": uuid.uuid4(),
                "node_id": node_id,
                "type": "markdown",
                "path": "/tmp/a3.md",
                "content": "# md",
                "summary": "md",
                "created_at": now,
            },
            {
                "id": uuid.uuid4(),
                "node_id": node_id,
                "type": "markdown",
                "path": "/tmp/a4.md",
                "content": "# md",
                "summary": "md",
                "created_at": now,
            },
        ],
    )
    await db_session.commit()

    r1 = await client.get(f"/nodes/{node_id}/artifacts", params={"limit": 1})
    link1 = r1.headers["Link"]
    assert 'rel="prev"' not in link1
    assert 'rel="next"' in link1 and 'offset=1' in link1

    r2 = await client.get(f"/nodes/{node_id}/artifacts", params={"limit": 1, "offset": 1})
    link2 = r2.headers["Link"]
    assert 'rel="prev"' in link2 and 'offset=0' in link2
    assert 'rel="next"' in link2 and 'offset=2' in link2

    r3 = await client.get(f"/nodes/{node_id}/artifacts", params={"limit": 1, "offset": 2})
    link3 = r3.headers["Link"]
    assert 'rel="next"' not in link3
    assert 'rel="prev"' in link3 and 'offset=1' in link3


@pytest.mark.asyncio
async def test_events_link_headers(client, seed_sample, db_session):
    run_id = seed_sample["run_id"]
    now = dt.datetime.now(dt.timezone.utc)
    await db_session.execute(
        insert(Event).values(
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": None,
                "level": "INFO",
                "message": "extra",
                "timestamp": now,
                "request_id": "req-3",
            }
        )
    )
    await db_session.commit()

    r1 = await client.get("/events", params={"run_id": run_id, "limit": 1})
    link1 = r1.headers["Link"]
    assert 'rel="prev"' not in link1
    assert 'rel="next"' in link1 and 'offset=1' in link1

    r2 = await client.get(
        "/events",
        params={"run_id": run_id, "limit": 1, "offset": 1},
    )
    link2 = r2.headers["Link"]
    assert 'rel="prev"' in link2 and 'offset=0' in link2
    assert 'rel="next"' in link2 and 'offset=2' in link2

    r3 = await client.get(
        "/events",
        params={"run_id": run_id, "limit": 1, "offset": 2},
    )
    link3 = r3.headers["Link"]
    assert 'rel="next"' not in link3
    assert 'rel="prev"' in link3 and 'offset=1' in link3
