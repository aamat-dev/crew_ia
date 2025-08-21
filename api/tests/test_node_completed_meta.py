# api/tests/test_node_completed_meta.py
import asyncio, json, pytest

@pytest.mark.asyncio
async def test_node_completed_has_meta(async_client):
    r = await async_client.post("/tasks",
        headers={"X-API-Key":"test-key"},
        json={
            "title":"Meta",
            "task":{"title":"Meta","plan":[{"id":"n1","title":"T1"}]},
            "options":{"resume":False,"dry_run":False,"override":[]}
        }
    )
    rid = r.json()["run_id"]
    for _ in range(80):
        rs = await async_client.get(f"/runs/{rid}", headers={"X-API-Key":"test-key"})
        if rs.json()["status"] in ("completed","failed"):
            break
        await asyncio.sleep(0.06)

    ev = await async_client.get(f"/runs/{rid}/events", headers={"X-API-Key":"test-key"})
    msgs = [e["message"] for e in ev.json()["items"] if e["level"]=="NODE_COMPLETED"]
    assert msgs, "missing NODE_COMPLETED"
    meta = json.loads(msgs[0])
    # selon dispo DB/FS, au moins un des champs doit exister
    assert any(k in meta for k in ("provider","model","latency_ms")), meta
