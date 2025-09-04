import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.plan import Plan, PlanStatus


@pytest.mark.asyncio
async def test_start_task_happy_path(async_client: AsyncClient, db_session: AsyncSession):
    task = Task(title="T1", status=TaskStatus.ready)
    db_session.add(task)
    await db_session.flush()
    plan = Plan(task_id=task.id, status=PlanStatus.ready, graph={})
    db_session.add(plan)
    await db_session.flush()
    task.plan_id = plan.id
    await db_session.commit()

    r = await async_client.post(f"/tasks/{task.id}/start", headers={"X-API-Key": "test-key"})
    assert r.status_code == 202
    data = r.json()
    run_id = uuid.UUID(data["run_id"])
    assert data["dry_run"] is False
    await db_session.refresh(task)
    assert task.run_id == run_id
    assert task.status == TaskStatus.running


@pytest.mark.asyncio
async def test_start_task_dry_run(async_client: AsyncClient, db_session: AsyncSession):
    task = Task(title="T2", status=TaskStatus.ready)
    db_session.add(task)
    await db_session.flush()
    plan = Plan(task_id=task.id, status=PlanStatus.ready, graph={})
    db_session.add(plan)
    await db_session.flush()
    task.plan_id = plan.id
    await db_session.commit()

    r = await async_client.post(
        f"/tasks/{task.id}/start", params={"dry_run": "true"}, headers={"X-API-Key": "test-key"}
    )
    assert r.status_code == 202
    data = r.json()
    uuid.UUID(data["run_id"])
    assert data["dry_run"] is True

    refreshed = await db_session.get(Task, task.id)
    assert refreshed.run_id is None
    assert refreshed.status == TaskStatus.ready


@pytest.mark.asyncio
@pytest.mark.parametrize("setup", ["missing", "invalid"])
async def test_start_task_plan_conflict(setup, async_client: AsyncClient, db_session: AsyncSession):
    task = Task(title="T3", status=TaskStatus.ready)
    db_session.add(task)
    await db_session.flush()

    if setup == "invalid":
        plan = Plan(task_id=task.id, status=PlanStatus.draft, graph={})
        db_session.add(plan)
        await db_session.flush()
        task.plan_id = plan.id
    await db_session.commit()

    r = await async_client.post(f"/tasks/{task.id}/start", headers={"X-API-Key": "test-key"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_start_task_not_found(async_client: AsyncClient):
    r = await async_client.post(f"/tasks/{uuid.uuid4()}/start", headers={"X-API-Key": "test-key"})
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_start_task_request_id(async_client: AsyncClient, db_session: AsyncSession):
    task = Task(title="T4", status=TaskStatus.ready)
    db_session.add(task)
    await db_session.flush()
    plan = Plan(task_id=task.id, status=PlanStatus.ready, graph={})
    db_session.add(plan)
    await db_session.flush()
    task.plan_id = plan.id
    await db_session.commit()

    headers = {"X-API-Key": "test-key", "X-Request-ID": "req-42"}
    r = await async_client.post(f"/tasks/{task.id}/start", headers=headers)
    assert r.status_code == 202
    assert r.headers.get("X-Request-ID") == "req-42"
