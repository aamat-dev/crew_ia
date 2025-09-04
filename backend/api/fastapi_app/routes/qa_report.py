from __future__ import annotations
import statistics
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.fastapi_app.deps import get_session
from backend.api.fastapi_app.models.run import Run
from backend.api.fastapi_app.models.node import Node
from backend.api.fastapi_app.models.feedback import Feedback

router = APIRouter(prefix="/runs", tags=["qa"])

def _decision_from_eval(evaluation: Dict[str, Any]) -> str:
    return (evaluation or {}).get("decision") or "revise"

@router.get("/{run_id}/qa-report")
async def get_qa_report(run_id: UUID, db: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    q = (
        select(Feedback, Node)
        .join(Node, Node.id == Feedback.node_id)
        .where(Feedback.run_id == run_id)
        .where(Feedback.source == "auto")
    )
    res = (await db.execute(q)).all()

    nodes: List[Dict[str, Any]] = []
    by_type: Dict[str, List[int]] = {}
    decisions: List[str] = []

    for fb, node in res:
        score = int(fb.score or 0)
        evaluation = fb.evaluation or {}
        decision = _decision_from_eval(evaluation)
        failed = evaluation.get("failed_criteria", [])
        node_type = getattr(node, "role", None)
        nodes.append({
            "node_id": str(node.id),
            "type": node_type,
            "score": score,
            "decision": decision,
            "failed_criteria": failed,
            "feedback_id": str(fb.id),
            "created_at": fb.created_at.isoformat() if getattr(fb, "created_at", None) else None,
        })
        if node_type is not None:
            by_type.setdefault(node_type, []).append(score)
        decisions.append(decision)

    scores = [n["score"] for n in nodes]
    if scores:
        mean = sum(scores) / len(scores)
        try:
            median = statistics.median(scores)
            p95 = statistics.quantiles(scores, n=20)[18]
        except Exception:
            median = scores[len(scores)//2]
            p95 = max(scores)
    else:
        mean = median = p95 = 0

    total = len(decisions)
    accept_rate = (sum(1 for d in decisions if d == "accept") / total) if total else 0
    reject_rate = (sum(1 for d in decisions if d == "reject") / total) if total else 0

    by_node_type = {
        t: {
            "mean": (sum(v) / len(v)) if v else 0,
            "count": len(v),
            "accept_rate": (sum(1 for n in nodes if n["type"] == t and n["decision"] == "accept") / len(v)) if v else 0,
            "reject_rate": (sum(1 for n in nodes if n["type"] == t and n["decision"] == "reject") / len(v)) if v else 0,
        }
        for t, v in by_type.items()
    }

    return {
        "run_id": str(run.id),
        "global": {
            "mean": round(mean, 2),
            "median": median,
            "p95": p95,
            "accept_rate": round(accept_rate, 2),
            "reject_rate": round(reject_rate, 2),
        },
        "by_node_type": by_node_type,
        "nodes": nodes,
    }
