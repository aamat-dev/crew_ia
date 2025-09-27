import uuid
import pytest
from sqlalchemy.dialects.postgresql import insert

from api.database.models import Task, Plan
from backend.app.models.plan_version import PlanVersion


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


@pytest.mark.asyncio
async def test_plan_version_diff(client, db_session):
    task_id = uuid.uuid4()
    await db_session.execute(insert(Task).values(id=task_id, title="Diff task", status="draft"))
    await db_session.commit()

    graph_v1 = {
        "version": "1.0",
        "plan": [
            {
                "id": "n1",
                "title": "Analyse",
                "deps": [],
                "suggested_agent_role": "analyst",
            }
        ],
        "edges": [],
    }

    create_resp = await client.post("/plans", json={"task_id": str(task_id), "graph": graph_v1})
    assert create_resp.status_code == 201
    plan_id = create_resp.json()["plan_id"]

    graph_v2 = {
        "version": "1.0",
        "plan": [
            {
                "id": "n1",
                "title": "Analyse approfondie",
                "deps": [],
                "suggested_agent_role": "analyst",
            },
            {
                "id": "n2",
                "title": "Synthèse",
                "deps": ["n1"],
                "suggested_agent_role": "writer",
            },
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
        ],
    }

    await db_session.execute(
        insert(PlanVersion).values(
            id=uuid.uuid4(),
            plan_id=plan_id,
            numero_version=2,
            graph=graph_v2,
            reason="auto-regenerated",
        )
    )
    await db_session.commit()

    diff_resp = await client.get(f"/plans/{plan_id}/versions/2/diff")
    assert diff_resp.status_code == 200
    diff = diff_resp.json()
    assert diff["current_version"] == 2
    assert diff["previous_version"] == 1
    assert len(diff["added_nodes"]) == 1
    assert diff["added_nodes"][0]["id"] == "n2"
    assert len(diff["removed_nodes"]) == 0
    assert len(diff["changed_nodes"]) == 1
    change_entry = diff["changed_nodes"][0]
    assert change_entry["id"] == "n1"
    assert "title" in change_entry["changes"]
    assert diff["added_edges"] == [{"source": "n1", "target": "n2"}]
    assert diff["removed_edges"] == []

    # Diff with explicit previous param
    diff_resp_prev = await client.get(f"/plans/{plan_id}/versions/2/diff?previous=1")
    assert diff_resp_prev.status_code == 200
    assert diff_resp_prev.json() == diff
