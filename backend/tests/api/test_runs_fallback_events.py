import datetime as dt
import uuid

import pytest
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete

from api.database.models import Run, Event


@pytest.mark.asyncio
async def test_get_run_reflects_completed_from_events(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    # Run resté en statut running sans ended_at
    await db_session.execute(
        insert(Run).values(
            id=run_id,
            title="R1",
            status="running",
            started_at=now,
        )
    )
    # Event final déjà présent (race condition)
    await db_session.execute(
        insert(Event).values(
            id=uuid.uuid4(),
            run_id=run_id,
            node_id=None,
            timestamp=now,
            level="RUN_COMPLETED",
            message="{}",
            request_id=None,
        )
    )
    await db_session.commit()

    r = await client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    # cleanup
    await db_session.execute(delete(Event).where(Event.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_run_reflects_failed_from_events(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    await db_session.execute(
        insert(Run).values(
            id=run_id,
            title="R2",
            status="queued",
            started_at=now,
        )
    )
    await db_session.execute(
        insert(Event).values(
            id=uuid.uuid4(),
            run_id=run_id,
            node_id=None,
            timestamp=now,
            level="RUN_FAILED",
            message="{}",
            request_id=None,
        )
    )
    await db_session.commit()

    r = await client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "failed"

    # cleanup
    await db_session.execute(delete(Event).where(Event.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()

