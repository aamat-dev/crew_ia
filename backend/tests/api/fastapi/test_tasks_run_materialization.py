import uuid
import pytest
from api.database.models import Run


@pytest.mark.asyncio
async def test_post_tasks_materializes_run_in_db(async_client, db_session):
    payload = {
        "title": "Mat-Run",
        "task": {"title": "Mat-Run", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }
    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-mat-1"}

    r = await async_client.post("/tasks", headers=headers, json=payload)
    assert r.status_code == 202
    body = r.json()
    run_id = body["run_id"]
    assert body["location"] == f"/runs/{run_id}"
    assert r.headers.get("Location") == f"/runs/{run_id}"

    # Vérifie matérialisation immédiate en DB
    run_uuid = uuid.UUID(run_id)
    db_run = await db_session.get(Run, run_uuid)
    assert db_run is not None
    # Statut initial tolérant: pending/queued/running, ou completed si l'exécution s'est terminée très vite
    status = getattr(db_run.status, "value", db_run.status)
    assert status in {"pending", "running", "queued", "completed"}
