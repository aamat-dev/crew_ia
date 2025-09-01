import uuid

import pytest
from sqlalchemy import insert, select

from app.models.task import Task, TaskStatus
from app.models.plan import Plan, PlanStatus
from app.models.plan_review import PlanReview
from app.schemas.plan import PlanGraph, PlanNode, PlanGenerationResult
import api.fastapi_app.routes.tasks as tasks_routes


@pytest.mark.asyncio
async def test_generate_plan_draft(client, db_session, monkeypatch):
    task_id = uuid.uuid4()
    await db_session.execute(
        insert(Task).values({"id": task_id, "title": "Demo", "status": TaskStatus.draft})
    )
    await db_session.commit()

    async def fake_generate(_task: Task) -> PlanGenerationResult:
        node = PlanNode(id="n1", title="T1", deps=[], suggested_agent_role="role")
        graph = PlanGraph(nodes=[node], edges=[])
        return PlanGenerationResult(graph=graph, status=PlanStatus.draft)

    monkeypatch.setattr(tasks_routes, "generate_plan", fake_generate)

    r = await client.post(f"/tasks/{task_id}/plan", headers={"X-API-Key": "test-key"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "draft"
    assert body["graph"]["version"] == "1.0"
    plan_id = uuid.UUID(body["plan_id"])

    plan = (
        await db_session.execute(select(Plan).where(Plan.id == plan_id))
    ).scalar_one()
    task = await db_session.get(Task, task_id)
    assert task.plan_id == plan.id
    assert plan.status == PlanStatus.draft


@pytest.mark.asyncio
async def test_generate_plan_invalid(client, db_session, monkeypatch):
    task_id = uuid.uuid4()
    await db_session.execute(
        insert(Task).values({"id": task_id, "title": "Demo", "status": TaskStatus.draft})
    )
    await db_session.commit()

    async def fake_generate(_task: Task) -> PlanGenerationResult:
        graph = PlanGraph()  # graph vide
        return PlanGenerationResult(graph=graph, status=PlanStatus.invalid)

    monkeypatch.setattr(tasks_routes, "generate_plan", fake_generate)

    r = await client.post(f"/tasks/{task_id}/plan", headers={"X-API-Key": "test-key"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "invalid"
    assert body["graph"]["version"] == "1.0"
    plan_id = uuid.UUID(body["plan_id"])
    plan = (
        await db_session.execute(select(Plan).where(Plan.id == plan_id))
    ).scalar_one()
    task = await db_session.get(Task, task_id)
    assert task.plan_id is None
    assert plan.status == PlanStatus.invalid


@pytest.mark.asyncio
async def test_submit_plan_validation(client, db_session, monkeypatch):
    task_id = uuid.uuid4()
    await db_session.execute(
        insert(Task).values({"id": task_id, "title": "Demo", "status": TaskStatus.draft})
    )
    await db_session.commit()

    async def fake_generate(_task: Task) -> PlanGenerationResult:
        node = PlanNode(id="n1", title="T1", deps=[], suggested_agent_role="role")
        graph = PlanGraph(nodes=[node], edges=[])
        return PlanGenerationResult(graph=graph, status=PlanStatus.draft)

    monkeypatch.setattr(tasks_routes, "generate_plan", fake_generate)

    r = await client.post(f"/tasks/{task_id}/plan", headers={"X-API-Key": "test-key"})
    plan_id = uuid.UUID(r.json()["plan_id"])

    r2 = await client.post(
        f"/plans/{plan_id}/submit_for_validation",
        json={"validated": True},
        headers={"X-API-Key": "test-key"},
    )
    assert r2.status_code == 200
    assert r2.json()["validated"] is True

    plan = await db_session.get(Plan, plan_id)
    assert plan.status == PlanStatus.ready

    reviews = (
        await db_session.execute(select(PlanReview).where(PlanReview.plan_id == plan_id))
    ).scalars().all()
    assert len(reviews) == 1
    assert reviews[0].validated is True
    assert reviews[0].version == 1


@pytest.mark.asyncio
async def test_plan_regeneration_after_review(client, db_session, monkeypatch):
    task_id = uuid.uuid4()
    await db_session.execute(
        insert(Task).values({"id": task_id, "title": "Demo", "status": TaskStatus.draft})
    )
    await db_session.commit()

    async def fake_generate(_task: Task) -> PlanGenerationResult:
        node = PlanNode(id="n1", title="T1", deps=[], suggested_agent_role="role")
        graph = PlanGraph(nodes=[node], edges=[])
        return PlanGenerationResult(graph=graph, status=PlanStatus.draft)

    monkeypatch.setattr(tasks_routes, "generate_plan", fake_generate)

    r = await client.post(f"/tasks/{task_id}/plan", headers={"X-API-Key": "test-key"})
    plan_id = uuid.UUID(r.json()["plan_id"])

    await client.post(
        f"/plans/{plan_id}/submit_for_validation",
        json={"validated": False, "errors": ["oops"]},
        headers={"X-API-Key": "test-key"},
    )

    # Regenerate plan -> version should increment
    r2 = await client.post(f"/tasks/{task_id}/plan", headers={"X-API-Key": "test-key"})
    assert r2.status_code == 201

    plan = await db_session.get(Plan, plan_id)
    assert plan.version == 2
    assert plan.status == PlanStatus.draft

    reviews = (
        await db_session.execute(select(PlanReview).where(PlanReview.plan_id == plan_id))
    ).scalars().all()
    assert len(reviews) == 1
    assert reviews[0].validated is False


@pytest.mark.asyncio
async def test_generate_plan_task_not_found(client):
    r = await client.post(f"/tasks/{uuid.uuid4()}/plan", headers={"X-API-Key": "test-key"})
    assert r.status_code == 404
