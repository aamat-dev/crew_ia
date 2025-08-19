from __future__ import annotations

import datetime as dt
from uuid import UUID
from typing import Any, Dict, Optional

from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Run, RunStatus, Node, NodeStatus
from core.events.publisher import EventPublisher
from core.events.types import EventType
from core.planning.task_graph import TaskGraph
from apps.orchestrator.executor import run_graph

import json
from pathlib import Path
import logging
log = logging.getLogger("orchestrator.api_runner")

def _read_llm_sidecar(run_id: str, node_id: str) -> Dict[str, Any]:
    """Lit le sidecar .llm.json pour extraire provider/model/latency/usage."""
    try:
        path = Path(".runs") / run_id / "nodes" / node_id / f"artifact_{node_id}.llm.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

async def run_task(
    run_id: str,
    task_spec: dict,
    options: Any,
    storage: CompositeAdapter,
    event_publisher: EventPublisher,
    title: str,
    request_id: Optional[str] = None,
):
    """
    Exécution d'un DAG réel avec émission d'events RUN_* / NODE_*.
    - run_id est fourni (UUID string)
    - storage est le CompositeAdapter (DB + fichiers)
    - event_publisher écrit dans la table events (via storage)
    """
    started = dt.datetime.now(dt.timezone.utc)

    # --------- Construire le DAG ----------
    dag = TaskGraph.from_plan(task_spec)

    # --------- Callbacks pour la télémétrie ----------
    async def on_node_start(node, node_id_txt):
        saved = await storage.save_node(
            node=Node(
                run_id=UUID(run_id),
                key=getattr(node, "id", None) or (node.get("id") if isinstance(node, dict) else None),
                title=getattr(node, "title", "") or (node.get("title") if isinstance(node, dict) else ""),
                status=NodeStatus.running,
                started_at=dt.datetime.now(dt.timezone.utc),
                checksum=getattr(node, "checksum", None) or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )
        setattr(node, "db_id", getattr(saved, "id", None))
        await event_publisher.emit(
            EventType.NODE_STARTED,
            {"run_id": run_id, "node_id": str(getattr(saved, "id", None)), "request_id": request_id, "checksum": getattr(node, "checksum", None)},
        )

    async def on_node_end(node, node_id_txt, status: str):
        ended = dt.datetime.now(dt.timezone.utc)
        db_id = getattr(node, "db_id", None)
        await storage.save_node(
            node=Node(
                id=db_id,
                run_id=UUID(run_id),
                key=getattr(node, "id", None) or (node.get("id") if isinstance(node, dict) else None),
                title=getattr(node, "title", "") or (node.get("title") if isinstance(node, dict) else ""),
                status=NodeStatus.completed if status == "completed" else NodeStatus.failed,
                ended_at=ended,
                checksum=getattr(node, "checksum", None) or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )
        side = _read_llm_sidecar(run_id, node_id_txt)
        payload = {
            "run_id": run_id,
            "node_id": str(db_id) if db_id else None,
            "status": status.upper(),
            "request_id": request_id,
            "checksum": getattr(node, "checksum", None),
        }
        if isinstance(side, dict):
            payload.update({
                "provider": side.get("provider"),
                "model": side.get("model_used") or side.get("model"),
                "latency_ms": side.get("latency_ms"),
                "usage": side.get("usage"),
            })
        await event_publisher.emit(
            EventType.NODE_COMPLETED if status == "completed" else EventType.NODE_FAILED,
            payload,
        )

    # --------- Exécution DAG ----------
    try:
        await event_publisher.emit(
            EventType.RUN_STARTED, {"run_id": run_id, "title": title, "request_id": request_id}
        )
        res = await run_graph(
            dag,
            storage=storage,
            run_id=run_id,
            override_completed=set(options.override or []),
            dry_run=bool(getattr(options, "dry_run", False)),
            on_node_start=on_node_start,
            on_node_end=on_node_end,
        )
        ended = dt.datetime.now(dt.timezone.utc)
        final_status = RunStatus.completed if res.get("status") == "success" else RunStatus.failed
        await storage.save_run(run=Run(id=UUID(run_id), title=title, status=final_status, started_at=started, ended_at=ended))
        await event_publisher.emit(
            EventType.RUN_COMPLETED if final_status == RunStatus.completed else EventType.RUN_FAILED,
            {"run_id": run_id, "request_id": request_id},
        )
    except Exception as e:  # pragma: no cover
        log.exception("Background run failed for run_id=%s", run_id)
        ended = dt.datetime.now(dt.timezone.utc)
        await storage.save_run(run=Run(id=UUID(run_id), title=title, status=RunStatus.failed, started_at=started, ended_at=ended))
        await event_publisher.emit(
            EventType.RUN_FAILED,
            {"run_id": run_id, "request_id": request_id, "error_class": e.__class__.__name__, "message": str(e)},
        )
