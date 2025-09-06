import json
import pytest
import uuid
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event
from .conftest import wait_status

@pytest.mark.asyncio
async def test_events_include_llm_metadata(client, db_session):
    payload = {
        "title": "LLMMeta",
        "task": {"title": "LLMMeta", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []}
    }
    r = await client.post("/tasks", json=payload, headers={"X-API-Key": "test-key"})
    assert r.status_code == 202
    rid = r.json()["run_id"]
    run_uuid = uuid.UUID(rid)

    # poll
    assert await wait_status(client, rid, "completed", timeout=5.0)
    rr = await client.get(f"/runs/{rid}", headers={"X-API-Key": "test-key"})

    ev = await client.get("/events", params={"run_id": rid}, headers={"X-API-Key": "test-key"})

    assert ev.status_code == 200
    items = ev.json()["items"]
    node_completed = [e for e in items if e["level"] == "NODE_COMPLETED"]
    assert node_completed, "NODE_COMPLETED event missing"
    # payload est dans e["message"] (JSON string)
    msg = json.loads(node_completed[0]["message"])
    assert isinstance(msg, dict)

    # nettoyage des données créées pendant le test
    await db_session.execute(delete(Event).where(Event.run_id == run_uuid))
    await db_session.execute(
        delete(Artifact).where(
            Artifact.node_id.in_(select(Node.id).where(Node.run_id == run_uuid))
        )
    )
    await db_session.execute(delete(Node).where(Node.run_id == run_uuid))
    await db_session.execute(delete(Run).where(Run.id == run_uuid))
    await db_session.commit()
