import datetime as dt
import uuid
import pytest
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete

from backend.api.fastapi_app.models.run import Run
from backend.api.fastapi_app.models.node import Node
from backend.api.fastapi_app.models.feedback import Feedback


@pytest.mark.asyncio
async def test_qa_report_aggregates(client, db_session):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()
    node_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    node_roles = ["write", "write", "research"]

    await db_session.execute(
        insert(Run.__table__),
        [{
            "id": run_id,
            "title": "Run QA",
            "status": "completed",
            "started_at": now,
            "ended_at": now,
        }],
    )

    await db_session.execute(
        insert(Node.__table__),
        [
            {"id": node_ids[0], "run_id": run_id, "role": node_roles[0], "title": "N1", "status": "completed"},
            {"id": node_ids[1], "run_id": run_id, "role": node_roles[1], "title": "N2", "status": "completed"},
            {"id": node_ids[2], "run_id": run_id, "role": node_roles[2], "title": "N3", "status": "completed"},
        ],
    )

    await db_session.execute(
        insert(Feedback.__table__),
        [
            {"id": uuid.uuid4(), "run_id": run_id, "node_id": node_ids[0], "source": "auto", "reviewer": "agent:qa", "score": 90, "comment": "ok", "evaluation": {
                "spec_version": "1.0.0",
                "checklist_id": "qa.write.v1",
                "checklist_version": "1.0.0",
                "node": {"id": str(node_ids[0]), "type": "write", "run_id": str(run_id)},
                "overall_score": 90,
                "decision": "accept",
                "per_criterion": [],
                "summary_comment": "ok",
                "failed_criteria": [],
            }, "created_at": now},
            {"id": uuid.uuid4(), "run_id": run_id, "node_id": node_ids[1], "source": "auto", "reviewer": "agent:qa", "score": 72, "comment": "revise", "evaluation": {
                "spec_version": "1.0.0",
                "checklist_id": "qa.write.v1",
                "checklist_version": "1.0.0",
                "node": {"id": str(node_ids[1]), "type": "write", "run_id": str(run_id)},
                "overall_score": 72,
                "decision": "revise",
                "per_criterion": [],
                "summary_comment": "revise",
                "failed_criteria": ["clarity"],
            }, "created_at": now},
            {"id": uuid.uuid4(), "run_id": run_id, "node_id": node_ids[2], "source": "auto", "reviewer": "agent:qa", "score": 55, "comment": "reject", "evaluation": {
                "spec_version": "1.0.0",
                "checklist_id": "qa.research.v1",
                "checklist_version": "1.0.0",
                "node": {"id": str(node_ids[2]), "type": "research", "run_id": str(run_id)},
                "overall_score": 55,
                "decision": "reject",
                "per_criterion": [],
                "summary_comment": "reject",
                "failed_criteria": ["sources", "depth"],
            }, "created_at": now},
        ],
    )
    await db_session.commit()

    r = await client.get(f"/runs/{run_id}/qa-report")
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] == str(run_id)
    assert data["global"]["accept_rate"] > 0
    assert "write" in data["by_node_type"]
    assert len(data["nodes"]) == 3
    n2 = next(n for n in data["nodes"] if n["node_id"] == str(node_ids[1]))
    assert "clarity" in n2["failed_criteria"]

    await db_session.execute(delete(Feedback).where(Feedback.run_id == run_id))
    await db_session.execute(delete(Node).where(Node.run_id == run_id))
    await db_session.execute(delete(Run).where(Run.id == run_id))
    await db_session.commit()
