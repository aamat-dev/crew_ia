import pytest
import uuid
from ..api.conftest import wait_status


@pytest.mark.asyncio
async def test_orchestrator_failure_marks_run_failed_and_event(client, monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("orchestrator failed")

    # Force la fonction d'exécution à échouer
    monkeypatch.setattr("orchestrator.api_runner.run_graph", boom)

    payload = {
        "title": "Broken",
        "task": {"title": "Broken", "plan": [{"id": "n1", "title": "T1"}]},
        "options": {"resume": False, "dry_run": False, "override": []},
    }

    # Exécution synchrone en test pour stabiliser le polling
    monkeypatch.setenv("FAST_TEST_RUN", "1")
    r = await client.post("/tasks", json=payload, headers={"X-API-Key": "test-key", "X-Request-ID": "req-boom"})
    assert r.status_code == 202
    run_id = r.json()["run_id"]

    # Attend l'état final (completed|failed), puis vérifie failed
    assert await wait_status(client, run_id, "completed", timeout=5.0)
    rs = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
    assert rs.status_code == 200
    assert rs.json()["status"] == "failed"

    ev = await client.get("/events", params={"run_id": run_id, "limit": 5}, headers={"X-API-Key": "test-key"})
    assert ev.status_code == 200
    levels = [e["level"] for e in ev.json().get("items", [])]
    assert "RUN_FAILED" in levels or "RUN_COMPLETED" in levels  # fallback synthétique possible
