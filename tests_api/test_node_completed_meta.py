# api/tests/test_node_completed_meta.py
import asyncio, json, pytest, uuid
from sqlalchemy import delete, select
from api.database.models import Run, Node, Artifact, Event

@pytest.mark.asyncio
async def test_node_completed_has_meta(async_client, db_session):
    r = await async_client.post("/tasks",
        headers={"X-API-Key":"test-key"},
        json={
            "title":"Meta",
            "task":{"title":"Meta","plan":[{"id":"n1","title":"T1"}]},
            "options":{"resume":False,"dry_run":False,"override":[]}
        }
    )
    rid = r.json()["run_id"]
    run_uuid = uuid.UUID(rid)
    for _ in range(80):
        rs = await async_client.get(f"/runs/{rid}", headers={"X-API-Key":"test-key"})
        if rs.json()["status"] in ("completed","failed"):
            break
        await asyncio.sleep(0.06)

    ev = await async_client.get(
        "/events", params={"run_id": rid}, headers={"X-API-Key": "test-key"}
    )
    msgs = [e["message"] for e in ev.json()["items"] if e["level"]=="NODE_COMPLETED"]

    assert msgs, "missing NODE_COMPLETED"
    meta = json.loads(msgs[0])
    assert isinstance(meta, dict)

    # nettoyage de la base pour éviter les effets de bord
    await db_session.execute(delete(Event).where(Event.run_id == run_uuid))
    await db_session.execute(
        delete(Artifact).where(
            Artifact.node_id.in_(select(Node.id).where(Node.run_id == run_uuid))
        )
    )
    await db_session.execute(delete(Node).where(Node.run_id == run_uuid))
    await db_session.execute(delete(Run).where(Run.id == run_uuid))
    await db_session.commit()
