import json, pytest, uuid
from ..conftest import wait_status
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event

@pytest.mark.asyncio
async def test_request_id_propagation(async_client, db_session):
    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-123"}
    payload = {
        "title": "Demo",
        "task_spec": {"title": "Demo", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    run_id = r.json()["run_id"]
    run_uuid = uuid.UUID(run_id)

    assert await wait_status(async_client, run_id, "completed", timeout=5.0)
    rs = await async_client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})

    events = await async_client.get("/events", params={"run_id": run_id}, headers={"X-API-Key": "test-key"})
    assert events.status_code == 200
    items = events.json()["items"]
    assert any(json.loads(e["message"]).get("request_id") == "req-123" for e in items)

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
