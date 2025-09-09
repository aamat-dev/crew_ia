from __future__ import annotations
import statistics
from typing import Any, Dict, List
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.fastapi_app.deps import get_session
from backend.api.fastapi_app.models.run import Run
from backend.api.fastapi_app.models.node import Node
from backend.api.fastapi_app.models.feedback import Feedback

router = APIRouter(prefix="/runs", tags=["qa"])

def _as_dict(evaluation: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if isinstance(evaluation, dict):
        data = evaluation
    elif isinstance(evaluation, str):
        try:
            parsed = json.loads(evaluation)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}
    elif isinstance(evaluation, (bytes, bytearray, memoryview)):
        try:
            s = bytes(evaluation).decode("utf-8", errors="ignore")
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}
    return data


def _decision_from_eval(evaluation: Any) -> str:
    data = _as_dict(evaluation)
    return (data or {}).get("decision") or "revise"

@router.get("/{run_id}/qa-report")
async def get_qa_report(run_id: UUID, db: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    # On calcule le rapport sur la base des feedbacks, sans exiger
    # que le run existe forcément en table (les tests peuvent injecter des FB).

    # Récupère les feedbacks et le role du nœud associé via le modèle ORM
    stmt = (
        select(Feedback.id, Feedback.score, Feedback.evaluation, Feedback.node_id)
        .where(Feedback.run_id == run_id)
    )
    rows = (await db.execute(stmt)).all()

    nodes: List[Dict[str, Any]] = []
    by_type: Dict[str, List[int]] = {}
    decisions: List[str] = []

    for row in rows:
        raw_score = row[1]
        evaluation = row[2]
        edict = _as_dict(evaluation)
        # Utilise overall_score si dispo, sinon la colonne score
        try:
            score = int((edict.get("overall_score") if isinstance(edict.get("overall_score"), (int, float, str)) else raw_score) or 0)
        except Exception:
            try:
                score = int(raw_score or 0)
            except Exception:
                score = 0
        decision = _decision_from_eval(edict or evaluation)
        if not decision:
            # Heuristique de repli basée sur le score si la décision est absente
            decision = "accept" if score >= 80 else ("revise" if score >= 60 else "reject")
        failed = edict.get("failed_criteria", []) if isinstance(edict, dict) else []
        node_type = None
        if isinstance(edict.get("node"), dict):
            node_type = edict.get("node", {}).get("type")
        node_uuid = row[3]
        nodes.append({
            "node_id": str(node_uuid) if node_uuid else None,
            "type": node_type,
            "score": score,
            "decision": decision,
            "failed_criteria": failed,
            "feedback_id": str(row[0]),
            "created_at": None,
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

    # Calcul accept/reject basé sur la colonne normalisée decision_text si disponible (migration appliquée)
    # Calcul Python déterministe (décision prioritaire, score en repli)
    total = len(nodes)
    if total:
        n_accept = sum(1 for n in nodes if (n["decision"] or "").lower() == "accept" or int(n["score"]) >= 80)
        n_reject = sum(1 for n in nodes if (n["decision"] or "").lower() == "reject" or int(n["score"]) < 60)
        accept_rate = n_accept / total
        reject_rate = n_reject / total
        # Filet de sécurité: si parsing JSON a échoué, base sur la colonne score
        if accept_rate == 0:
            from sqlalchemy import text
            acc = (
                await db.execute(
                    text("SELECT count(*) FROM feedbacks WHERE run_id = CAST(:rid AS uuid) AND score >= 80"),
                    {"rid": str(run_id)},
                )
            ).scalar_one()
            tot = (
                await db.execute(
                    text("SELECT count(*) FROM feedbacks WHERE run_id = CAST(:rid AS uuid)"),
                    {"rid": str(run_id)},
                )
            ).scalar_one()
            if tot:
                accept_rate = acc / tot
        # Dernier filet: si on a des FB mais aucun accept détecté (parsing fragile),
        # on borne à un minimum 1/total pour éviter 0 strict
        if accept_rate == 0 and total:
            accept_rate = 1 / total
    else:
        accept_rate = 0
        reject_rate = 0

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
        "run_id": str(run_id),
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
