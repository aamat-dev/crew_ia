import uuid
import pytest
from sqlalchemy import insert, select

from api.database.models import Plan, Task, Assignment


@pytest.mark.asyncio
async def test_assignments_upsert(client, db_session):
    plan_id = uuid.uuid4()
    task_id = uuid.uuid4()
    graph = {"plan": [{"id": "n1"}]}

    await db_session.execute(insert(Task).values(id=task_id, title="t", status="draft"))
    await db_session.execute(
        insert(Plan).values(id=plan_id, task_id=task_id, status="draft", graph=graph)
    )
    await db_session.commit()

    payload = {
        "items": [
            {
                "node_id": "n1",
                "role": "writer",
                "agent_id": "a1",
                "llm_backend": "openai",
                "llm_model": "gpt-4",
            }
        ]
    }
    r = await client.post(f"/plans/{plan_id}/assignments", json=payload)
    assert r.status_code == 200
    assert r.json()["updated"] == 1

    stmt = select(Assignment).where(Assignment.plan_id == plan_id)
    res = await db_session.execute(stmt)
    row = res.scalar_one()
    assert row.role == "writer"

    payload["items"][0]["role"] = "editor"
    r2 = await client.post(f"/plans/{plan_id}/assignments", json=payload)
    assert r2.status_code == 200
    assert r2.json()["items"][0]["role"] == "editor"

    db_session.expire_all()
    res2 = await db_session.execute(stmt)
    row2 = res2.scalar_one()
    assert row2.role == "editor"

    r3 = await client.post(f"/plans/{plan_id}/assignments", json=payload)
    assert r3.status_code == 200
    res3 = await db_session.execute(stmt)
    assert res3.scalar_one().role == "editor"


@pytest.mark.asyncio
async def test_assignments_unknown_node(client, db_session):
    plan_id = uuid.uuid4()
    task_id = uuid.uuid4()
    graph = {"plan": [{"id": "n1"}]}
    await db_session.execute(insert(Task).values(id=task_id, title="t", status="draft"))
    await db_session.execute(
        insert(Plan).values(id=plan_id, task_id=task_id, status="draft", graph=graph)
    )
    await db_session.commit()

    payload = {
        "items": [
            {
                "node_id": "n2",
                "role": "writer",
                "agent_id": "a1",
                "llm_backend": "openai",
                "llm_model": "gpt-4",
            }
        ]
    }
    r = await client.post(f"/plans/{plan_id}/assignments", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_assignments_plan_not_found(client):
    payload = {
        "items": [
            {
                "node_id": "n1",
                "role": "writer",
                "agent_id": "a1",
                "llm_backend": "openai",
                "llm_model": "gpt-4",
            }
        ]
    }
    r = await client.post(f"/plans/{uuid.uuid4()}/assignments", json=payload)
    assert r.status_code == 404
