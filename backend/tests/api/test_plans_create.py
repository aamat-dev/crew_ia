import uuid
import pytest
from sqlalchemy.dialects.postgresql import insert

from api.database.models import Task, Plan


@pytest.mark.asyncio
async def test_create_and_get_plan(client, db_session):
    # Préparer une tâche en DB
    task_id = uuid.uuid4()
    await db_session.execute(
        insert(Task).values(id=task_id, title="T-plan", status="draft")
    )
    await db_session.commit()

    graph = {
        "version": "1.0",
        "nodes": [
            {
                "id": "n1",
                "title": "Node 1",
                "deps": [],
                "suggested_agent_role": "writer",
                "acceptance": [],
                "risks": [],
                "assumptions": [],
                "notes": [],
            }
        ],
        "edges": [],
    }

    # Créer un plan
    r = await client.post("/plans", json={"task_id": str(task_id), "graph": graph})
    assert r.status_code == 201
    body = r.json()
    plan_id = body["plan_id"]
    assert body["status"] in ("draft", {"draft": "draft"}.get("draft"))

    # Vérifier qu'il existe en DB
    row = await db_session.get(Plan, plan_id)
    assert row is not None
    assert row.task_id == task_id

    # Récupérer le plan
    r2 = await client.get(f"/plans/{plan_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["id"] == plan_id
    assert data["task_id"] == str(task_id)
    assert data["graph"]["version"] == "1.0"

