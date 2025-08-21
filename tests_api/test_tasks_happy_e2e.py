import asyncio, json, pytest

@pytest.mark.asyncio
async def test_post_tasks_and_follow(async_client):
    # 202 + run_id
    r = await async_client.post("/tasks",
        headers={"X-API-Key":"test-key"},
        json={
            "title":"Demo",
            "task":{"title":"Demo","plan":[{"id":"n1","title":"T1"}]},
            "options":{"resume":False,"dry_run":False,"override":[]}
        }
    )
    assert r.status_code == 202
    rid = r.json()["run_id"]

    # poll jusqu'à fin
    for _ in range(80):
        rs = await async_client.get(f"/runs/{rid}", headers={"X-API-Key":"test-key"})
        if rs.json()["status"] in ("completed","failed"):
            break
        await asyncio.sleep(0.05)

    # checks de base
    nodes = await async_client.get(f"/runs/{rid}/nodes", headers={"X-API-Key":"test-key"})
    assert nodes.status_code == 200
    events = await async_client.get(f"/runs/{rid}/events", headers={"X-API-Key":"test-key"})
    assert events.status_code == 200
    assert any(e["level"].startswith("RUN_") for e in events.json()["items"])
