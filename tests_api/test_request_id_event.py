import asyncio, json, pytest

@pytest.mark.asyncio
async def test_request_id_propagation(async_client):
    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-123"}
    payload = {
        "title": "Demo",
        "task_spec": {"title": "Demo", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    run_id = r.json()["run_id"]

    for _ in range(80):
        rs = await async_client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
        if rs.json()["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)

    events = await async_client.get("/events", params={"run_id": run_id}, headers={"X-API-Key": "test-key"})
    assert events.status_code == 200
    items = events.json()["items"]
    assert any(json.loads(e["message"]).get("request_id") == "req-123" for e in items)
