# apps/orchestrator/api_runner.py
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
import os

log = logging.getLogger("orchestrator.api_runner")

def _extract_llm_meta_from_artifacts(artifacts: list[dict]) -> dict:
    """
    Cherche dans les artifacts DB un JSON contenant provider/model/latency/usage.
    On tente 'content' JSON ; à défaut si 'path' pointe vers un .llm.json on le lit.
    """
    # 1) contenu JSON direct
    for a in artifacts:
        c = a.get("content")
        if not c:
            continue
        try:
            obj = json.loads(c)
        except Exception:
            continue
        if isinstance(obj, dict) and ("provider" in obj or "model" in obj or "latency_ms" in obj):
            return {
                "provider": obj.get("provider"),
                "model": obj.get("model_used") or obj.get("model"),
                "latency_ms": obj.get("latency_ms"),
                "usage": obj.get("usage"),
            }
    # 2) chemin .llm.json éventuel
    for a in artifacts:
        p = a.get("path")
        if not p or not str(p).endswith(".llm.json"):
            continue
        try:
            obj = json.loads(Path(p).read_text(encoding="utf-8"))
            return {
                "provider": obj.get("provider"),
                "model": obj.get("model_used") or obj.get("model"),
                "latency_ms": obj.get("latency_ms"),
                "usage": obj.get("usage"),
            }
        except Exception:
            pass
    return {}

def _read_llm_sidecar_fs(run_id: str, node_key: str, runs_root: str = None) -> dict:
    """Lit un sidecar ``artifact_<node_key>.llm.json``.

    La racine de recherche est, par ordre de priorité :
    ``runs_root`` si fourni, puis ``ARTIFACTS_DIR``, ``RUNS_ROOT``
    et enfin ``.runs``.  Retourne un ``dict`` si le fichier existe,
    sinon ``{}``.
    """
    base = runs_root or os.getenv("ARTIFACTS_DIR") or os.getenv("RUNS_ROOT") or ".runs"
    path = Path(base) / run_id / "nodes" / node_key / f"artifact_{node_key}.llm.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
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
    started = dt.datetime.now(dt.timezone.utc)

    # 1) Construire DAG
    if not task_spec.get("plan") and task_spec.get("type") == "demo":
        # Plan minimal de démonstration
        task_spec = {"plan": [{"id": "n1", "title": title}]}
    dag = TaskGraph.from_plan(task_spec)

    # 2) Callbacks télémétrie
    node_ids: dict[str, UUID] = {}

    async def on_node_start(node, node_key: str):
        """Persiste un nœud au démarrage et mémorise son UUID."""
        node_db = await storage.save_node(
            node=Node(
                run_id=UUID(run_id),
                key=node_key,
                title=getattr(node, "title", "") or (node.get("title") if isinstance(node, dict) else ""),
                status=NodeStatus.running,
                checksum=getattr(node, "checksum", None) or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )
        node_ids[node_key] = node_db.id
        # permet à agent_runner de retrouver l'id DB
        try:
            setattr(node, "db_id", node_db.id)
        except Exception:
            pass
        await event_publisher.emit(
            EventType.NODE_STARTED,
            {
                "run_id": run_id,
                "node_key": node_key,
                "request_id": request_id,
                "checksum": getattr(node, "checksum", None),
            },
        )

    async def on_node_end(node, node_key: str, status: str):
        ended = dt.datetime.now(dt.timezone.utc)
        node_id = node_ids.get(node_key)
        await storage.save_node(
            node=Node(
                id=node_id,
                run_id=UUID(run_id),
                key=node_key,
                title=getattr(node, "title", "") or (node.get("title") if isinstance(node, dict) else ""),
                status=NodeStatus.completed if status == "completed" else NodeStatus.failed,
                updated_at=ended,
                checksum=getattr(node, "checksum", None) or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )

        # 1) Essaye via DB: logical_id -> node_id -> artifacts
        meta = {}
        node_db_id = node_id
        try:
            # méthode optionnelle selon l'adapter; on tente si dispo
            if node_db_id is None and hasattr(storage, "get_node_id_by_logical"):
                node_db_id = await storage.get_node_id_by_logical(run_id, node_key)
            # si on a un id DB, on liste les artifacts (si dispo)
            if node_db_id and hasattr(storage, "list_artifacts_for_node"):
                artifacts = await storage.list_artifacts_for_node(node_db_id)
                meta = _extract_llm_meta_from_artifacts(artifacts) or {}
        except Exception:
            # on n'échoue pas l'exécution pour de la télémétrie
            meta = {}

        # 2) Fallback FS
        if not meta:
            meta = _read_llm_sidecar_fs(run_id, node_key) or {}

        payload = {
            "run_id": run_id,
            "node_key": node_key,
            "status": status.upper(),
            "request_id": request_id,
            "checksum": getattr(node, "checksum", None),
        }
        if meta:
            payload.update({
                "provider": meta.get("provider"),
                "model": meta.get("model"),
                "latency_ms": meta.get("latency_ms"),
                "usage": meta.get("usage"),
            })

        await event_publisher.emit(
            EventType.NODE_COMPLETED if status == "completed" else EventType.NODE_FAILED,
            payload,
        )

    # 3) Exécution DAG + events de run
    try:
        await event_publisher.emit(
            EventType.RUN_STARTED, {"run_id": run_id, "title": title, "request_id": request_id}
        )

        res = await run_graph(
            dag,
            storage=storage,
            run_id=run_id,
            override_completed=set(getattr(options, "override", []) or []),
            dry_run=bool(getattr(options, "dry_run", False)),
            on_node_start=on_node_start,
            on_node_end=on_node_end,
        )

        ended = dt.datetime.now(dt.timezone.utc)
        final_status = RunStatus.completed if res.get("status") == "success" else RunStatus.failed
        await storage.save_run(
            run=Run(id=UUID(run_id), title=title, status=final_status, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(
            EventType.RUN_COMPLETED if final_status == RunStatus.completed else EventType.RUN_FAILED,
            {"run_id": run_id, "request_id": request_id},
        )
    except Exception as e:  # pragma: no cover
        log.exception("Background run failed for run_id=%s", run_id)
        ended = dt.datetime.now(dt.timezone.utc)
        await storage.save_run(
            run=Run(id=UUID(run_id), title=title, status=RunStatus.failed, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(
            EventType.RUN_FAILED,
            {"run_id": run_id, "request_id": request_id, "error_class": e.__class__.__name__, "message": str(e)},
        )
