from __future__ import annotations
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime
import os
import json
from pathlib import Path
import math
from statistics import mean

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import (
    get_session,
    read_timezone,
    to_tz,
    strict_api_key_auth,
    cap_date_range,
    settings,
)
from ..schemas_base import (
    Page,
    RunListItemOut,
    RunOut,
    RunSummaryOut,
    NodeOut,
    DagOut,
    ArtifactOut,
    RunIncidentOut,
    RunIncidentRunOut,
    IncidentNodeOut,
    IncidentEventOut,
)
from ..schemas_base import EventOut as EventOutSchema
from ..schemas.feedbacks import FeedbackOut
from backend.api.utils.pagination import (
    PaginationParams,
    pagination_params,
    set_pagination_headers,
)
from ..ordering import apply_order

# Import des modèles ORM existants
from core.storage.db_models import (
    Run,
    Node,
    Artifact,
    Event,
    Feedback,
    RunStatus,
    NodeStatus,
    AuditLog,
    AuditSource,
)  # type: ignore
from core.events.types import EventType
from backend.orchestrator import orchestrator_adapter as orch
from pydantic import BaseModel, Field

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(strict_api_key_auth)])

# Helpers
ORDERABLE_FIELDS = {
    "created_at": Run.created_at,
    "started_at": Run.started_at,
    "ended_at": Run.ended_at,
    "title": Run.title,
    "status": Run.status,
}


def _safe_json_loads(payload: str | None) -> dict:
    if not payload:
        return {}
    try:
        data = json.loads(payload)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _meta_to_dict(meta: Any) -> dict[str, Any]:
    if isinstance(meta, dict):
        return meta
    if isinstance(meta, str):
        try:
            data = json.loads(meta)
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _extract_llm_usage(message: str | None) -> Tuple[int, int, Optional[float]]:
    data = _safe_json_loads(message)
    usage = data.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0
    try:
        prompt_tokens = int(prompt_tokens)
    except Exception:
        prompt_tokens = 0
    try:
        completion_tokens = int(completion_tokens)
    except Exception:
        completion_tokens = 0
    latency_raw = data.get("latency_ms") or usage.get("latency_ms")
    try:
        latency = float(latency_raw)
    except Exception:
        latency = None
    return prompt_tokens, completion_tokens, latency


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    values_sorted = sorted(values)
    if len(values_sorted) == 1:
        return values_sorted[0]
    k = (len(values_sorted) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values_sorted[int(k)]
    return values_sorted[f] + (values_sorted[c] - values_sorted[f]) * (k - f)


def _artifact_preview(content: Optional[str], summary: Optional[str]) -> Optional[str]:
    if summary:
        return summary
    if not content:
        return None
    first_line = content.strip().splitlines()[:1]
    if not first_line:
        return None
    snippet = first_line[0][:240]
    return snippet if snippet else None


async def _collect_llm_metrics(
    session: AsyncSession, run_id: UUID
) -> Tuple[int, int, int, int, Optional[float], Optional[float]]:
    usage_rows = (
        await session.execute(
            select(Event.message)
            .where(
                Event.run_id == run_id,
                Event.level == EventType.NODE_COMPLETED.value,
            )
        )
    ).scalars().all()
    llm_prompt_tokens = 0
    llm_completion_tokens = 0
    llm_request_count = 0
    latencies: List[float] = []
    for message in usage_rows:
        prompt, completion, latency = _extract_llm_usage(message)
        if prompt or completion or latency is not None:
            llm_request_count += 1
        llm_prompt_tokens += prompt
        llm_completion_tokens += completion
        if latency is not None:
            latencies.append(latency)
    llm_total_tokens = llm_prompt_tokens + llm_completion_tokens
    llm_avg_latency = mean(latencies) if latencies else None
    llm_p95_latency = _percentile(latencies, 0.95)
    return (
        llm_prompt_tokens,
        llm_completion_tokens,
        llm_total_tokens,
        llm_request_count,
        llm_avg_latency,
        llm_p95_latency,
    )


class RunActionPayload(BaseModel):
    action: str


def _record_audit(
    session: AsyncSession,
    *,
    run_id: UUID,
    request: Request,
    action: str,
    metadata: dict | None = None,
) -> None:
    actor_role = request.headers.get("X-Role")
    actor = request.headers.get("X-Actor") or request.headers.get("X-User")
    request_id = getattr(request.state, "request_id", None)
    session.add(
        AuditLog(
            run_id=run_id,
            source=AuditSource.human,
            action=action,
            actor_role=actor_role,
            actor=actor,
            request_id=request_id,
            payload=metadata,
        )
    )

@router.patch("/{run_id}")
async def run_action(
    run_id: UUID,
    request: Request,
    payload: RunActionPayload = Body(...),
    session: AsyncSession = Depends(get_session),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    action = (payload.action or "").lower()
    allowed = {"cancel", "pause", "resume", "skip_failed_and_resume"}
    if action not in allowed:
        raise HTTPException(status_code=400, detail="unknown action")

    from ..utils.run_flow import utcnow

    if action == "cancel":
        if run.status in {RunStatus.completed, RunStatus.failed, RunStatus.canceled}:
            raise HTTPException(status_code=409, detail="run already ended")
        try:
            run.status = RunStatus.canceled
            run.ended_at = utcnow()
            session.add(run)
            session.add(
                Event(
                    run_id=run.id,
                    level=EventType.RUN_CANCELED.value,
                    message=json.dumps({"reason": "canceled"}),
                )
            )
            _record_audit(
                session,
                run_id=run_id,
                request=request,
                action="run.cancel",
                metadata={"payload": payload.model_dump(exclude_none=True)},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="DB update failed")
        try:
            await orch.cancel(run_id)
        except Exception:
            pass
        return {"status": RunStatus.canceled.value}

    if action == "pause":
        if run.status != RunStatus.running:
            raise HTTPException(status_code=409, detail="run not running")
        try:
            run.status = RunStatus.paused
            session.add(run)
            session.add(
                Event(
                    run_id=run.id,
                    level=EventType.RUN_PAUSED.value,
                    message=json.dumps({"reason": "manual"}),
                )
            )
            _record_audit(
                session,
                run_id=run_id,
                request=request,
                action="run.pause",
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="DB update failed")
        try:
            await orch.pause(run_id)
        except Exception:
            pass
        return {"status": RunStatus.paused.value}

    if action == "resume":
        if run.status != RunStatus.paused:
            raise HTTPException(status_code=409, detail="run not paused")
        try:
            run.status = RunStatus.running
            session.add(run)
            session.add(
                Event(
                    run_id=run.id,
                    level=EventType.RUN_RESUMED.value,
                    message=json.dumps({"reason": "manual"}),
                )
            )
            _record_audit(
                session,
                run_id=run_id,
                request=request,
                action="run.resume",
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="DB update failed")
        try:
            await orch.resume(run_id)
        except Exception:
            pass
        return {"status": RunStatus.running.value}

    # skip_failed_and_resume
    failed_nodes = (
        await session.execute(
            select(Node).where(Node.run_id == run_id, Node.status == NodeStatus.failed)
        )
    ).scalars().all()
    if not failed_nodes:
        raise HTTPException(status_code=400, detail="no failed nodes to skip")
    skipped_ids: list[str] = []
    now = utcnow()
    try:
        for node in failed_nodes:
            node.status = NodeStatus.skipped
            node.updated_at = now
            session.add(node)
            skipped_ids.append(str(node.id))
        run.status = RunStatus.completed
        run.ended_at = now
        session.add(run)
        session.add(
            Event(
                run_id=run.id,
                level=EventType.RUN_COMPLETED.value,
                message=json.dumps({"reason": "skip_failed_and_resume", "skipped_nodes": skipped_ids}),
            )
        )
        _record_audit(
            session,
            run_id=run_id,
            request=request,
            action="run.skip_failed_and_resume",
            metadata={"skipped_nodes": skipped_ids},
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="DB update failed")
    return {"status": RunStatus.completed.value, "skipped_nodes": skipped_ids}

@router.get("", response_model=Page[RunListItemOut])
async def list_runs(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    tz = Depends(read_timezone),
    pagination: PaginationParams = Depends(pagination_params),
    status: Optional[str] = Query(None, description="Filtre par status"),
    title_contains: Optional[str] = Query(None, description="Filtre par sous-chaîne du titre"),
    started_from: Optional[datetime] = Query(None),
    started_to: Optional[datetime] = Query(None),
):
    cap_date_range(started_from, started_to)
    where_clauses = []
    if status:
        where_clauses.append(Run.status == status)
    if title_contains:
        like = f"%{title_contains}%"
        where_clauses.append(Run.title.ilike(like))
    if started_from:
        where_clauses.append(Run.started_at >= started_from)
    if started_to:
        where_clauses.append(Run.started_at <= started_to)

    base = select(Run)
    if where_clauses:
        base = base.where(and_(*where_clauses))

    total = (
        await session.execute(
            select(func.count(Run.id)).select_from(Run).where(and_(*where_clauses))
            if where_clauses
            else select(func.count(Run.id)).select_from(Run)
        )
    ).scalar_one()

    stmt = apply_order(
        base,
        pagination.order_by,
        pagination.order_dir,
        ORDERABLE_FIELDS,
        "-created_at",
    ).limit(pagination.limit).offset(pagination.offset)
    runs = (await session.execute(stmt)).scalars().all()

    items = [
        RunListItemOut(
            id=r.id,
            title=r.title,
            status=r.status,
            started_at=to_tz(r.started_at, tz),
            ended_at=to_tz(getattr(r, "ended_at", None), tz),
        )
        for r in runs
    ]

    limit = pagination.limit
    offset = pagination.offset
    links_dict = set_pagination_headers(
        response, request, total, limit, offset
    )

    return Page[RunListItemOut](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        links=links_dict or None,
    )

@router.get("/{run_id}", response_model=RunOut)
async def get_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    tz=Depends(read_timezone),
    include_events: int | None = Query(
        None,
        description="Inclure les N derniers événements (ex: 10). Laisse vide pour ne pas inclure.",
        ge=1,
        le=200,
    ),
    include_nodes: bool = Query(
        False,
        description="Inclure le DAG avec les nœuds et feedbacks associés (défaut: false).",
    ),
    include_artifacts: int | None = Query(
        None,
        description="Inclure les N derniers artifacts du run (ordre anti-chronologique).",
        ge=1,
        le=50,
    ),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Normalise le type (Enum -> str) pour une comparaison fiable
    status = run.status.value if hasattr(run.status, "value") else run.status

    # 1) Evénements finaux (source prioritaire)
    final_event_level: Optional[str] = None
    final_event_ts: Optional[datetime] = None
    if status in ("queued", "running", "canceled", "paused"):
        evt_row = (
            await session.execute(
                select(Event.level, Event.timestamp)
                .where(
                    Event.run_id == run_id,
                    Event.level.in_(
                        [
                            EventType.RUN_COMPLETED.value,
                            EventType.RUN_FAILED.value,
                            EventType.RUN_CANCELED.value,
                            EventType.RUN_PAUSED.value,
                            EventType.RUN_RESUMED.value,
                        ]
                    ),
                )
                .order_by(Event.timestamp.desc())
                .limit(1)
            )
        ).first()
        if evt_row:
            final_event_level, final_event_ts = evt_row
            if final_event_level == EventType.RUN_COMPLETED.value:
                status = RunStatus.completed.value
            elif final_event_level == EventType.RUN_FAILED.value:
                status = RunStatus.failed.value
            elif final_event_level == EventType.RUN_CANCELED.value:
                status = RunStatus.canceled.value
            elif final_event_level == EventType.RUN_PAUSED.value:
                status = RunStatus.paused.value
            elif final_event_level == EventType.RUN_RESUMED.value:
                status = RunStatus.running.value

    # 2) Comptage des nœuds (si pas d'événement final déterminant)
    nodes_q = select(func.count()).select_from(Node).where(Node.run_id == run_id)
    nodes_total = (await session.execute(nodes_q)).scalar_one()
    nodes_completed = (
        await session.execute(
            select(func.count()).select_from(Node).where(
                Node.run_id == run_id, Node.status == "completed"
            )
        )
    ).scalar_one()
    nodes_failed = (
        await session.execute(
            select(func.count()).select_from(Node).where(
                Node.run_id == run_id, Node.status == "failed"
            )
        )
    ).scalar_one()
    if status in ("queued", "running") and not final_event_level:
        if nodes_total and (nodes_completed + nodes_failed == nodes_total):
            status = "completed" if nodes_failed == 0 else "failed"
        elif nodes_total <= 1:
            # Cas mono‑nœud: si un event NODE_* final est déjà visible, refléter son statut
            last_node_evt = (
                await session.execute(
                    select(Event.level, Event.timestamp)
                    .where(
                        Event.run_id == run_id,
                        Event.level.in_(["NODE_COMPLETED", "NODE_FAILED"]),
                    )
                    .order_by(Event.timestamp.desc())
                    .limit(1)
                )
            ).first()
            if last_node_evt:
                lvl, _ts = last_node_evt
                if lvl == "NODE_COMPLETED":
                    status = "completed"
                elif lvl == "NODE_FAILED":
                    status = "failed"

    # 3) Fallback fichier (si rien de concluant)
    if status in ("queued", "running") and not final_event_level:
        try:
            runs_root = Path(os.getenv("ARTIFACTS_DIR", settings.artifacts_dir))
            run_dir = runs_root / str(run_id)
            # a) run.json explicite
            try:
                meta = json.loads((run_dir / "run.json").read_text())
                if isinstance(meta, dict) and meta.get("ended_at"):
                    s = (meta.get("status") or "completed").lower()
                    if s in ("completed", "failed"):
                        status = s
            except Exception:
                pass
            # b) En l'absence de run.json, présence d'un sidecar LLM sur un nœud unique
            if status in ("queued", "running") and nodes_total <= 1:
                nodes_dir = run_dir / "nodes"
                # Cherche un artifact *.llm.json qui indiquerait la fin d'un nœud
                if nodes_dir.exists():
                    has_sidecar = any(p.name.endswith(".llm.json") for p in nodes_dir.rglob("artifact_*.llm.json"))
                    if has_sidecar:
                        status = "completed"
        except Exception:
            # tolérant aux erreurs: on reste sur le statut courant
            pass

    # Compteurs annexes
    artifacts_total = (
        await session.execute(
            select(func.count(Artifact.id))
            .select_from(Artifact)
            .join(Node, Artifact.node_id == Node.id)
            .where(Node.run_id == run_id)
        )
    ).scalar_one()
    events_total = (
        await session.execute(select(func.count()).select_from(Event).where(Event.run_id == run_id))
    ).scalar_one()

    usage_rows = (
        await session.execute(
            select(Event.message)
            .where(
                Event.run_id == run_id,
                Event.level == EventType.NODE_COMPLETED.value,
            )
        )
    ).scalars().all()
    llm_prompt_tokens = 0
    llm_completion_tokens = 0
    llm_request_count = 0
    latencies: List[float] = []
    for message in usage_rows:
        prompt, completion, latency = _extract_llm_usage(message)
        if prompt or completion or latency is not None:
            llm_request_count += 1
        llm_prompt_tokens += prompt
        llm_completion_tokens += completion
        if latency is not None:
            latencies.append(latency)
    llm_total_tokens = llm_prompt_tokens + llm_completion_tokens
    llm_avg_latency = mean(latencies) if latencies else None
    llm_p95_latency = _percentile(latencies, 0.95)

    # Duration
    started = getattr(run, "started_at", None)
    ended = getattr(run, "ended_at", None)
    duration_ms = None
    if started and ended:
        duration_ms = int((ended - started).total_seconds() * 1000)
    elif started and final_event_ts is not None:
        try:
            duration_ms = int((final_event_ts - started).total_seconds() * 1000)
        except Exception:
            duration_ms = None
    dag: DagOut | None = None
    if include_nodes:
        node_rows = (
            await session.execute(select(Node).where(Node.run_id == run_id))
        ).scalars().all()
        node_ids = [n.id for n in node_rows]
        fb_map: dict[UUID, list[FeedbackOut]] = {nid: [] for nid in node_ids}
        if node_ids:
            fb_rows = (
                await session.execute(
                    select(Feedback)
                    .where(Feedback.node_id.in_(node_ids))
                    .order_by(Feedback.created_at.desc())
                )
            ).scalars().all()
            for f in fb_rows:
                fb_map[f.node_id].append(
                    FeedbackOut(
                        id=f.id,
                        run_id=f.run_id,
                        node_id=f.node_id,
                        source=f.source,
                        reviewer=f.reviewer,
                        score=f.score,
                        comment=f.comment,
                        metadata=f.meta,
                        created_at=to_tz(f.created_at, tz),
                        updated_at=to_tz(getattr(f, "updated_at", None), tz),
                    )
                )

        dag_nodes = [
            NodeOut(
                id=n.id,
                run_id=n.run_id,
                key=n.key,
                title=n.title,
                status=n.status,
                role=n.role,
                checksum=n.checksum,
                deps=n.deps,
                created_at=to_tz(n.created_at, tz),
                updated_at=to_tz(n.updated_at, tz),
                feedbacks=fb_map.get(n.id, []),
            )
            for n in node_rows
        ]
        dag = DagOut(nodes=dag_nodes, edges=[])

    artifacts_embedded: list[ArtifactOut] | None = None
    if include_artifacts:
        artifact_rows = (
            await session.execute(
                select(Artifact, Node)
                .join(Node, Artifact.node_id == Node.id)
                .where(Node.run_id == run_id)
                .order_by(Artifact.created_at.desc())
                .limit(include_artifacts)
            )
        ).all()
        artifacts_embedded = []
        for artifact, node in artifact_rows:
            preview = _artifact_preview(artifact.content, artifact.summary)
            artifacts_embedded.append(
                ArtifactOut(
                    id=artifact.id,
                    node_id=artifact.node_id,
                    type=artifact.type,
                    path=artifact.path,
                    content=None,
                    summary=artifact.summary,
                    created_at=to_tz(artifact.created_at, tz),
                    preview=preview,
                )
            )

    # Événements récents (optionnel)
    events_embedded: list[EventOutSchema] | None = None
    if include_events:
        evt_rows = (
            await session.execute(
                select(Event)
                .where(Event.run_id == run_id)
                .order_by(Event.timestamp.desc())
                .limit(include_events)
            )
        ).scalars().all()
        events_embedded = [
            EventOutSchema(
                id=e.id,
                run_id=e.run_id,
                node_id=getattr(e, "node_id", None),
                level=e.level,
                message=e.message,
                timestamp=to_tz(e.timestamp, tz),
                request_id=getattr(e, "request_id", None),
            )
            for e in evt_rows
        ]

    return RunOut(
        id=run.id,
        title=run.title,
        status=status,
        started_at=to_tz(started, tz),
        ended_at=to_tz(ended, tz),
        summary=RunSummaryOut(
            nodes_total=nodes_total,
            nodes_completed=nodes_completed,
            nodes_failed=nodes_failed,
            artifacts_total=artifacts_total,
            events_total=events_total,
            duration_ms=duration_ms,
            llm_prompt_tokens=llm_prompt_tokens,
            llm_completion_tokens=llm_completion_tokens,
            llm_total_tokens=llm_total_tokens,
            llm_request_count=llm_request_count,
            llm_avg_latency_ms=round(llm_avg_latency, 2) if llm_avg_latency is not None else None,
            llm_p95_latency_ms=round(llm_p95_latency, 2) if llm_p95_latency is not None else None,
        ),
        dag=dag,
        events=events_embedded,
        artifacts=artifacts_embedded,
    )

@router.get("/{run_id}/summary", response_model=RunSummaryOut)
async def get_run_summary(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    nodes_total = (
        await session.execute(select(func.count()).select_from(Node).where(Node.run_id == run_id))
    ).scalar_one()
    nodes_completed = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "completed")
        )
    ).scalar_one()
    nodes_failed = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "failed")
        )
    ).scalar_one()
    artifacts_total = (
        await session.execute(
            select(func.count(Artifact.id))
            .select_from(Artifact)
            .join(Node, Artifact.node_id == Node.id)
            .where(Node.run_id == run_id)
        )
    ).scalar_one()
    events_total = (
        await session.execute(select(func.count()).select_from(Event).where(Event.run_id == run_id))
    ).scalar_one()

    duration_ms = None
    started = getattr(run, "started_at", None)
    ended = getattr(run, "ended_at", None)
    if started and ended:
        duration_ms = int((ended - started).total_seconds() * 1000)

    (
        llm_prompt_tokens,
        llm_completion_tokens,
        llm_total_tokens,
        llm_request_count,
        llm_avg_latency,
        llm_p95_latency,
    ) = await _collect_llm_metrics(session, run_id)

    return RunSummaryOut(
        nodes_total=nodes_total,
        nodes_completed=nodes_completed,
        nodes_failed=nodes_failed,
        artifacts_total=artifacts_total,
        events_total=events_total,
        duration_ms=duration_ms,
        llm_prompt_tokens=llm_prompt_tokens,
        llm_completion_tokens=llm_completion_tokens,
        llm_total_tokens=llm_total_tokens,
        llm_request_count=llm_request_count,
        llm_avg_latency_ms=round(llm_avg_latency, 2) if llm_avg_latency is not None else None,
        llm_p95_latency_ms=round(llm_p95_latency, 2) if llm_p95_latency is not None else None,
    )


@router.get("/{run_id}/incident", response_model=RunIncidentOut)
async def get_run_incident(
    run_id: UUID,
    export: bool = Query(False, description="Retourner le rapport en téléchargement."),
    session: AsyncSession = Depends(get_session),
    tz=Depends(read_timezone),
):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    nodes_total = (
        await session.execute(select(func.count()).select_from(Node).where(Node.run_id == run_id))
    ).scalar_one()
    nodes_completed = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "completed")
        )
    ).scalar_one()
    nodes_failed_total = (
        await session.execute(
            select(func.count()).select_from(Node).where(Node.run_id == run_id, Node.status == "failed")
        )
    ).scalar_one()
    artifacts_total = (
        await session.execute(
            select(func.count(Artifact.id))
            .select_from(Artifact)
            .join(Node, Artifact.node_id == Node.id)
            .where(Node.run_id == run_id)
        )
    ).scalar_one()
    events_total = (
        await session.execute(select(func.count()).select_from(Event).where(Event.run_id == run_id))
    ).scalar_one()

    started = getattr(run, "started_at", None)
    ended = getattr(run, "ended_at", None)
    duration_ms = None
    if started and ended:
        duration_ms = int((ended - started).total_seconds() * 1000)

    (
        llm_prompt_tokens,
        llm_completion_tokens,
        llm_total_tokens,
        llm_request_count,
        llm_avg_latency,
        llm_p95_latency,
    ) = await _collect_llm_metrics(session, run_id)

    summary = RunSummaryOut(
        nodes_total=nodes_total,
        nodes_completed=nodes_completed,
        nodes_failed=nodes_failed_total,
        artifacts_total=artifacts_total,
        events_total=events_total,
        duration_ms=duration_ms,
        llm_prompt_tokens=llm_prompt_tokens,
        llm_completion_tokens=llm_completion_tokens,
        llm_total_tokens=llm_total_tokens,
        llm_request_count=llm_request_count,
        llm_avg_latency_ms=round(llm_avg_latency, 2) if llm_avg_latency is not None else None,
        llm_p95_latency_ms=round(llm_p95_latency, 2) if llm_p95_latency is not None else None,
    )

    meta_dict = _meta_to_dict(getattr(run, "meta", None))
    signals = meta_dict.get("signals") if isinstance(meta_dict.get("signals"), list) else []

    failed_nodes_rows = (
        await session.execute(
            select(Node)
            .where(Node.run_id == run_id, Node.status == NodeStatus.failed)
            .order_by(Node.created_at.asc())
        )
    ).scalars().all()
    node_ids = [row.id for row in failed_nodes_rows]
    node_events_map: dict[UUID, list[IncidentEventOut]] = {nid: [] for nid in node_ids}
    node_artifacts_map: dict[UUID, list[ArtifactOut]] = {nid: [] for nid in node_ids}

    if node_ids:
        event_rows = (
            await session.execute(
                select(Event)
                .where(Event.node_id.in_(node_ids))
                .order_by(Event.timestamp.desc())
            )
        ).scalars().all()
        for evt in event_rows:
            nid = getattr(evt, "node_id", None)
            if nid in node_events_map and len(node_events_map[nid]) < 5:
                node_events_map[nid].append(
                    IncidentEventOut(
                        id=evt.id,
                        level=evt.level,
                        message=evt.message,
                        timestamp=to_tz(evt.timestamp, tz),
                        node_id=nid,
                    )
                )

        artifact_rows = (
            await session.execute(
                select(Artifact)
                .where(Artifact.node_id.in_(node_ids))
                .order_by(Artifact.created_at.desc())
            )
        ).scalars().all()
        for art in artifact_rows:
            nid = art.node_id
            if nid in node_artifacts_map and len(node_artifacts_map[nid]) < 3:
                node_artifacts_map[nid].append(
                    ArtifactOut(
                        id=art.id,
                        node_id=art.node_id,
                        type=art.type,
                        path=art.path,
                        content=None,
                        summary=art.summary,
                        created_at=to_tz(art.created_at, tz),
                        preview=_artifact_preview(art.content, art.summary),
                    )
                )

    failed_nodes_out = [
        IncidentNodeOut(
            id=node.id,
            key=node.key,
            title=node.title,
            status=str(node.status),
            role=node.role,
            updated_at=to_tz(node.updated_at, tz) if getattr(node, "updated_at", None) else None,
            events=node_events_map.get(node.id, []),
            artifacts=node_artifacts_map.get(node.id, []),
        )
        for node in failed_nodes_rows
    ]

    recent_events_rows = (
        await session.execute(
            select(Event)
            .where(
                Event.run_id == run_id,
                Event.level.in_(
                    [
                        EventType.RUN_FAILED.value,
                        EventType.NODE_FAILED.value,
                        "ERROR",
                    ]
                ),
            )
            .order_by(Event.timestamp.desc())
            .limit(20)
        )
    ).scalars().all()
    recent_events = [
        IncidentEventOut(
            id=evt.id,
            level=evt.level,
            message=evt.message,
            timestamp=to_tz(evt.timestamp, tz),
            node_id=getattr(evt, "node_id", None),
        )
        for evt in recent_events_rows
    ]

    incident = RunIncidentOut(
        run=RunIncidentRunOut(
            id=run.id,
            title=run.title,
            status=str(run.status.value if hasattr(run.status, "value") else run.status),
            started_at=to_tz(started, tz) if started else None,
            ended_at=to_tz(ended, tz) if ended else None,
            duration_ms=duration_ms,
            summary=summary,
        ),
        failed_nodes=failed_nodes_out,
        recent_events=recent_events,
        signals=[signal for signal in signals if isinstance(signal, dict)],
    )

    if export:
        payload = jsonable_encoder(incident)
        filename = f"run-{run_id}-incident.json"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return JSONResponse(content=payload, headers=headers)

    return incident
