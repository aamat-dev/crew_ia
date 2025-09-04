import pytest
import uuid
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event


@pytest.mark.asyncio
async def test_post_tasks_returns_run_id_and_location(async_client, db_session):
    payload = {
        "title": "Demo",
        "task": {"title": "Demo", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-123"}
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    body = r.json()
    run_id = body["run_id"]
    run_uuid = uuid.UUID(run_id)
    assert body["location"] == f"/runs/{run_id}"

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


@pytest.mark.asyncio
async def test_post_tasks_requires_api_key(client_noauth):
    payload = {"title": "x", "task": {"plan": [{"id": "n1", "title": "T1"}]}}
    r = await client_noauth.post("/tasks", json=payload)
    assert r.status_code == 401
