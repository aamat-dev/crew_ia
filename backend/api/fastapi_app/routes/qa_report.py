from __future__ import annotations
import statistics
from typing import Any, Dict, List
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.fastapi_app.deps import get_session, get_sessionmaker
from backend.api.fastapi_app.models.run import Run
from backend.api.fastapi_app.models.node import Node
from backend.api.fastapi_app.models.feedback import Feedback
from core.storage.postgres_adapter import PostgresAdapter

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
async def get_qa_report(
    run_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    # On calcule le rapport sur la base des feedbacks, sans exiger
    # que le run existe forcément en table (les tests peuvent injecter des FB).

    # Récupère les feedbacks et le role du nœud associé via le modèle ORM
    stmt = (
        select(
            Feedback.id,
            Feedback.score,
            Feedback.evaluation,
            Feedback.created_at,
            Feedback.node_id,
            Node.role.label("node_role"),
            Node.title.label("node_title"),
        )
        .join(Node, Node.id == Feedback.node_id, isouter=True)
        .where(Feedback.run_id == run_id)
    )
    rows = (await db.execute(stmt)).all()

    if not rows:
        try:
            override_get_sm = request.app.dependency_overrides.get(get_sessionmaker)  # type: ignore[attr-defined]
        except Exception:
            override_get_sm = None
        session_maker = None
        if callable(override_get_sm):
            try:
                session_maker = override_get_sm()
            except Exception:
                session_maker = None
        if session_maker is None:
            try:
                session_maker = get_sessionmaker()
            except Exception:
                session_maker = None
        if session_maker is not None:
            async with session_maker() as alt_session:
                rows = (await alt_session.execute(stmt)).all()

    if not rows:
        storage = getattr(request.app.state, "storage", None)
        pg_adapter = None
        if storage and hasattr(storage, "adapters"):
            for adapter in storage.adapters:
                if isinstance(adapter, PostgresAdapter):
                    pg_adapter = adapter
                    break
        if pg_adapter is not None:
            async with pg_adapter.session() as session:
                rows = (await session.execute(stmt)).all()

    nodes: List[Dict[str, Any]] = []
    by_type: Dict[str, List[int]] = {}

    for row in rows:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        raw_score = mapping[Feedback.score]
        evaluation = mapping[Feedback.evaluation]
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
        # Extraction robuste des critères échoués
        failed_raw = edict.get("failed_criteria", []) if isinstance(edict, dict) else []
        failed: List[str]
        if isinstance(failed_raw, list):
            failed = [str(x) for x in failed_raw]
        elif isinstance(failed_raw, (set, tuple)):
            failed = [str(x) for x in list(failed_raw)]
        elif isinstance(failed_raw, (bytes, bytearray, memoryview)):
            try:
                s = bytes(failed_raw).decode("utf-8", errors="ignore")
                parsed = json.loads(s)
                failed = [str(x) for x in parsed] if isinstance(parsed, list) else ([s] if s else [])
            except Exception:
                failed = []
        elif isinstance(failed_raw, str):
            # Peut être une représentation JSON de liste ou un simple label
            try:
                parsed = json.loads(failed_raw)
                failed = [str(x) for x in parsed] if isinstance(parsed, list) else ([failed_raw] if failed_raw else [])
            except Exception:
                failed = [failed_raw] if failed_raw else []
        else:
            failed = []
        node_type = None
        if isinstance(edict.get("node"), dict):
            node_type = edict.get("node", {}).get("type")
        if not node_type:
            node_role = mapping.get("node_role", None) if hasattr(mapping, "get") else getattr(row, "node_role", None)
            node_type = node_role

        node_uuid = mapping[Feedback.node_id]
        created_at = mapping[Feedback.created_at]
        feedback_id = mapping[Feedback.id]

        nodes.append({
            "node_id": str(node_uuid) if node_uuid else None,
            "type": node_type,
            "score": score,
            "decision": decision,
            "failed_criteria": failed,
            "feedback_id": str(feedback_id),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else None,
        })
        if node_type:
            by_type.setdefault(node_type, []).append(score)

    scores = [n["score"] for n in nodes]
    if scores:
        sorted_scores = sorted(scores)
        mean = sum(sorted_scores) / len(sorted_scores)
        try:
            median = statistics.median(sorted_scores)
        except statistics.StatisticsError:
            median = sorted_scores[len(sorted_scores) // 2]
        try:
            p95 = statistics.quantiles(sorted_scores, n=20)[18]
        except statistics.StatisticsError:
            p95 = max(sorted_scores)
    else:
        mean = median = p95 = 0

    # Calcul accept/reject basé sur la colonne normalisée decision_text si disponible (migration appliquée)
    # Calcul Python déterministe (décision prioritaire, score en repli)
    def _decision_equals(val: str, expected: str) -> bool:
        return (val or "").strip().lower() == expected

    total = len(nodes)
    if total:
        n_accept = sum(1 for n in nodes if _decision_equals(n["decision"], "accept"))
        n_reject = sum(1 for n in nodes if _decision_equals(n["decision"], "reject"))

        if n_accept == 0:
            n_accept = sum(1 for n in nodes if n.get("score", 0) >= 80)
        if n_reject == 0:
            n_reject = sum(1 for n in nodes if n.get("score", 0) < 60)

        accept_rate = n_accept / total if total else 0
        reject_rate = n_reject / total if total else 0
    else:
        accept_rate = 0
        reject_rate = 0

    by_node_type = {
        t: {
            "mean": (sum(v) / len(v)) if v else 0,
            "count": len(v),
            "accept_rate": (
                sum(1 for n in nodes if n["type"] == t and _decision_equals(n["decision"], "accept"))
                or sum(1 for n in nodes if n["type"] == t and n.get("score", 0) >= 80)
            ) / len(v) if v else 0,
            "reject_rate": (
                sum(1 for n in nodes if n["type"] == t and _decision_equals(n["decision"], "reject"))
                or sum(1 for n in nodes if n["type"] == t and n.get("score", 0) < 60)
            ) / len(v) if v else 0,
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
