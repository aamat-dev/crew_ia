import json
import json
import pytest
import datetime as dt
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from api.database.models import Run, Node, Event, Artifact
from core.storage.db_models import RunStatus, NodeStatus, AuditLog
from core.events.types import EventType

@pytest.mark.asyncio
async def test_list_runs(client, seed_sample):
    r = await client.get("/runs")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["title"] == "Sample Run" for item in data["items"])

@pytest.mark.asyncio
async def test_get_run_detail(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["nodes_total"] == 3
    assert body["summary"]["artifacts_total"] == 2
    assert body["summary"]["events_total"] == 2
    assert "llm_prompt_tokens" in body["summary"]


@pytest.mark.asyncio
async def test_get_run_include_nodes_toggle(client, seed_sample):
    run_id = seed_sample["run_id"]

    # Par défaut: pas de DAG embarqué
    base = await client.get(f"/runs/{run_id}")
    assert base.status_code == 200
    assert base.json()["dag"] is None

    # Avec include_nodes -> liste des nodes retournée
    with_nodes = await client.get(f"/runs/{run_id}?include_nodes=true")
    assert with_nodes.status_code == 200
    dag = with_nodes.json()["dag"]
    assert dag is not None
    assert len(dag["nodes"]) >= 1


@pytest.mark.asyncio
async def test_get_run_include_artifacts(client, seed_sample):
    run_id = seed_sample["run_id"]

    resp = await client.get(f"/runs/{run_id}?include_artifacts=2")
    assert resp.status_code == 200
    body = resp.json()
    artifacts = body.get("artifacts")
    assert artifacts is not None
    assert len(artifacts) == 2
    assert all("preview" in item for item in artifacts)


@pytest.mark.asyncio
async def test_get_run_summary_ok(client, seed_sample):
    run_id = seed_sample["run_id"]
    r = await client.get(f"/runs/{run_id}/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["nodes_total"] == 3
    assert body["nodes_completed"] == 2
    assert body["nodes_failed"] == 1
    assert body["artifacts_total"] == 2
    assert body["events_total"] == 2
    assert body["duration_ms"] == 300000
    assert "llm_prompt_tokens" in body


@pytest.mark.asyncio
async def test_title_filter(client, seed_sample):
    r = await client.get("/runs?title_contains=sample")
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.get("/runs?title_contains=nomatch")
    assert r.status_code == 200
    assert r.json()["total"] == 0

@pytest.mark.asyncio
async def test_auth_required(client_noauth):
    r = await client_noauth.get("/runs")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_runs_ordering(client, db_session, seed_sample):
    now = dt.datetime.now(dt.timezone.utc)
    run1 = {
        "id": uuid.uuid4(),
        "title": "Run1",
        "status": "completed",
        "started_at": now - dt.timedelta(minutes=10),
        "ended_at": now - dt.timedelta(minutes=9),
    }
    run2 = {
        "id": uuid.uuid4(),
        "title": "Run2",
        "status": "completed",
        "started_at": now - dt.timedelta(minutes=1),
        "ended_at": now,
    }
    await db_session.execute(insert(Run), [run1, run2])
    await db_session.commit()
    try:
        r = await client.get("/runs?order_by=started_at&order_dir=asc")
        times = [it["started_at"] for it in r.json()["items"][:3]]
        assert times == sorted(times)

        r = await client.get("/runs?order_by=-started_at")
        times_desc = [it["started_at"] for it in r.json()["items"][:3]]
        assert times_desc == sorted(times_desc, reverse=True)

        r = await client.get("/runs?order_by=foo")
        assert r.status_code == 422

        r = await client.get(
            "/runs?status=completed&order_by=started_at&order_dir=desc&offset=1&limit=1"
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["started_at"] == times_desc[1]
    finally:
        await db_session.execute(delete(Run).where(Run.id.in_([run1["id"], run2["id"]])))
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_run_summary_404(client):
    r = await client.get(f"/runs/{uuid.uuid4()}/summary")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cancel_run_emits_run_canceled_event(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()

    await db_session.execute(
        insert(Run).values(
            {
                "id": run_id,
                "title": "Cancelable Run",
                "status": RunStatus.running.value,
                "started_at": now,
            }
        )
    )
    await db_session.commit()

    try:
        resp = await client.patch(f"/runs/{run_id}", json={"action": "cancel"})
        assert resp.status_code == 200
        assert resp.json()["status"] == RunStatus.canceled.value

        run_row = (
            await db_session.execute(select(Run).where(Run.id == run_id))
        ).scalar_one()
        assert run_row.status == RunStatus.canceled

        events = (
            await db_session.execute(select(Event).where(Event.run_id == run_id))
        ).scalars().all()
        levels = {evt.level for evt in events}
        assert EventType.RUN_CANCELED.value in levels

        audit_resp = await client.get(f"/audit?run_id={run_id}")
        assert audit_resp.status_code == 200
        audit_items = audit_resp.json()["items"]
        assert any(entry["action"] == "run.cancel" for entry in audit_items)
        db_audit = (
            await db_session.execute(select(AuditLog).where(AuditLog.run_id == run_id))
        ).scalars().all()
        assert any(row.action == "run.cancel" for row in db_audit)
    finally:
        await db_session.execute(delete(Event).where(Event.run_id == run_id))
        await db_session.execute(delete(Run).where(Run.id == run_id))
        await db_session.commit()


@pytest.mark.asyncio
async def test_run_pause_resume(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    await db_session.execute(
        insert(Run).values(
            {
                "id": run_id,
                "title": "Run Pause",
                "status": RunStatus.running.value,
                "started_at": now,
            }
        )
    )
    await db_session.commit()

    pause_resp = await client.patch(f"/runs/{run_id}", json={"action": "pause"})
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == RunStatus.paused.value

    run_row = (
        await db_session.execute(
            select(Run)
            .where(Run.id == run_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert run_row.status == RunStatus.paused

    pause_event_levels = {
        evt.level
        for evt in (
            await db_session.execute(select(Event).where(Event.run_id == run_id))
        ).scalars().all()
    }
    assert EventType.RUN_PAUSED.value in pause_event_levels

    audit_pause = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.run_id == run_id, AuditLog.action == "run.pause")
        )
    ).scalars().all()
    assert audit_pause

    resume_resp = await client.patch(f"/runs/{run_id}", json={"action": "resume"})
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == RunStatus.running.value

    run_row = (
        await db_session.execute(
            select(Run)
            .where(Run.id == run_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert run_row.status == RunStatus.running

    resume_event_levels = {
        evt.level
        for evt in (
            await db_session.execute(select(Event).where(Event.run_id == run_id))
        ).scalars().all()
    }
    assert EventType.RUN_RESUMED.value in resume_event_levels

    audit_resume = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.run_id == run_id, AuditLog.action == "run.resume")
        )
    ).scalars().all()
    assert audit_resume

    await db_session.execute(delete(Event).where(Event.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_run_skip_failed_and_resume(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    node_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    await db_session.execute(
        insert(Run).values(
            {
                "id": run_id,
                "title": "Run Skip",
                "status": RunStatus.failed.value,
                "started_at": now - dt.timedelta(minutes=5),
                "ended_at": now,
            }
        )
    )
    await db_session.execute(
        insert(Node),
        [
            {
                "id": node_ids[0],
                "run_id": run_id,
                "key": "n1",
                "title": "Node 1",
                "status": NodeStatus.completed.value,
                "created_at": now - dt.timedelta(minutes=5),
            },
            {
                "id": node_ids[1],
                "run_id": run_id,
                "key": "n2",
                "title": "Node 2",
                "status": NodeStatus.failed.value,
                "created_at": now - dt.timedelta(minutes=4),
            },
            {
                "id": node_ids[2],
                "run_id": run_id,
                "key": "n3",
                "title": "Node 3",
                "status": NodeStatus.queued.value,
                "created_at": now - dt.timedelta(minutes=3),
            },
        ],
    )
    await db_session.commit()

    resp = await client.patch(f"/runs/{run_id}", json={"action": "skip_failed_and_resume"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == RunStatus.completed.value
    skipped_nodes = payload.get("skipped_nodes")
    assert skipped_nodes and all(isinstance(n, str) for n in skipped_nodes)

    nodes = (
        await db_session.execute(
            select(Node)
            .where(Node.run_id == run_id)
            .execution_options(populate_existing=True)
        )
    ).scalars().all()
    assert any(n.status == NodeStatus.skipped for n in nodes)

    run_row = (
        await db_session.execute(
            select(Run)
            .where(Run.id == run_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert run_row.status == RunStatus.completed
    assert run_row.ended_at is not None

    completion_events = (
        await db_session.execute(
            select(Event).where(Event.run_id == run_id, Event.level == EventType.RUN_COMPLETED.value)
        )
    ).scalars().all()
    assert any(json.loads(evt.message).get("reason") == "skip_failed_and_resume" for evt in completion_events)

    audit_entries = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.run_id == run_id, AuditLog.action == "run.skip_failed_and_resume"
            )
        )
    ).scalars().all()
    assert audit_entries

    await db_session.execute(delete(Event).where(Event.run_id == run_id))
    await db_session.execute(delete(Node).where(Node.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_audit_route_requires_filter(client):
    resp = await client.get("/audit")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_run_incident_report(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    node_failed = uuid.uuid4()
    node_ok = uuid.uuid4()

    await db_session.execute(
        insert(Run).values(
            id=run_id,
            title="Incident Run",
            status=RunStatus.failed.value,
            started_at=now - dt.timedelta(minutes=10),
            ended_at=now,
        )
    )
    run_row = await db_session.get(Run, run_id)
    assert run_row is not None
    run_row.meta = {
        "signals": [
            {"action": "plan_revision", "report": {"reason": "LLM timeout"}},
        ]
    }
    await db_session.flush()
    await db_session.execute(
        insert(Node),
        [
            {
                "id": node_failed,
                "run_id": run_id,
                "key": "analyse",
                "title": "Analyse",
                "status": NodeStatus.failed.value,
                "role": "analyst",
                "created_at": now - dt.timedelta(minutes=9),
                "updated_at": now - dt.timedelta(minutes=5),
            },
            {
                "id": node_ok,
                "run_id": run_id,
                "key": "synthese",
                "title": "Synthèse",
                "status": NodeStatus.completed.value,
                "role": "writer",
                "created_at": now - dt.timedelta(minutes=8),
                "updated_at": now - dt.timedelta(minutes=4),
            },
        ],
    )
    await db_session.execute(
        insert(Event),
        [
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": node_failed,
                "level": "NODE_FAILED",
                "message": json.dumps({"error": "timeout"}),
                "timestamp": now - dt.timedelta(minutes=5),
            },
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": node_failed,
                "level": "ERROR",
                "message": "Traceback...",
                "timestamp": now - dt.timedelta(minutes=5, seconds=10),
            },
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": None,
                "level": EventType.RUN_FAILED.value,
                "message": json.dumps({"reason": "timeout"}),
                "timestamp": now - dt.timedelta(minutes=4),
            },
        ],
    )
    await db_session.execute(
        insert(Artifact).values(
            id=uuid.uuid4(),
            node_id=node_failed,
            type="log",
            path="/tmp/log.txt",
            content="stack trace",
            created_at=now - dt.timedelta(minutes=5),
        )
    )
    await db_session.commit()

    resp = await client.get(f"/runs/{run_id}/incident")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run"]["id"] == str(run_id)
    assert body["run"]["status"].startswith("failed")
    assert body["run"]["summary"]["nodes_failed"] == 1
    assert len(body["failed_nodes"]) == 1
    node_info = body["failed_nodes"][0]
    assert node_info["events"]
    assert node_info["artifacts"]
    assert body["signals"]
    recent_levels = {evt["level"] for evt in body["recent_events"]}
    assert EventType.RUN_FAILED.value in recent_levels

    export_resp = await client.get(f"/runs/{run_id}/incident?export=true")
    assert export_resp.status_code == 200
    assert "attachment" in export_resp.headers.get("Content-Disposition", "")
