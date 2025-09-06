import json, pytest
from ..conftest import wait_status

import uuid
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event


@pytest.mark.asyncio
async def test_post_tasks_and_follow(async_client, db_session):
    # 202 + run_id
    r = await async_client.post(
        "/tasks",
        headers={"X-API-Key": "test-key"},
        json={
            "title": "Demo",
            "task": {"title": "Demo", "plan": [{"id": "n1", "title": "T1"}]},
            "options": {"resume": False, "dry_run": False, "override": []},
        },
    )
    assert r.status_code == 202
    rid = r.json()["run_id"]
    run_uuid = uuid.UUID(rid)

    # poll jusqu'à fin
    assert await wait_status(async_client, rid, "completed", timeout=5.0)
    rs = await async_client.get(f"/runs/{rid}", headers={"X-API-Key":"test-key"})

    # checks de base
    nodes = await async_client.get(f"/runs/{rid}/nodes", headers={"X-API-Key":"test-key"})
    assert nodes.status_code == 200
    events = await async_client.get(
        "/events", params={"run_id": rid}, headers={"X-API-Key": "test-key"}
    )
    assert events.status_code == 200
    assert any(e["level"].startswith("RUN_") for e in events.json()["items"])

    # nettoyage
    await db_session.execute(delete(Event).where(Event.run_id == run_uuid))
    await db_session.execute(
        delete(Artifact).where(
            Artifact.node_id.in_(select(Node.id).where(Node.run_id == run_uuid))
        )
    )
    await db_session.execute(delete(Node).where(Node.run_id == run_uuid))
    await db_session.execute(delete(Run).where(Run.id == run_uuid))
    await db_session.commit()
