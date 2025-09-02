import uuid
import datetime as dt
import pytest
from sqlalchemy import insert, delete

from api.fastapi_app.models.run import Run
from api.fastapi_app.models.node import Node
from api.fastapi_app.models.feedback import Feedback


@pytest.mark.asyncio
async def test_create_feedback_minimal(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    node_id = uuid.uuid4()

    await db_session.execute(insert(Run), [{
        "id": run_id,
        "title": "Run X",
        "status": "completed",
        "started_at": now,
        "ended_at": now,
    }])
    await db_session.execute(insert(Node), [{
        "id": node_id,
        "run_id": run_id,
        "role": "write",
        "title": "N1",
        "status": "completed",
    }])
    await db_session.commit()

    payload = {
        "run_id": str(run_id),
        "node_id": str(node_id),
        "source": "auto",
        "reviewer": "agent:qa-reviewer@v1",
        "score": 88,
        "comment": "ok",
        "evaluation": {"overall_score": 88, "decision": "accept"},
    }
    r = await client.post("/feedbacks", json=payload, headers={"X-Request-ID": "test-req"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["run_id"] == str(run_id)
    assert data["node_id"] == str(node_id)
    assert data["score"] == 88

    await db_session.execute(delete(Feedback).where(Feedback.run_id == run_id))
    await db_session.execute(delete(Node).where(Node.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()
