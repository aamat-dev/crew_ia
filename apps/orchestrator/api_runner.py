# apps/orchestrator/api_runner.py
from __future__ import annotations

import datetime as dt
import uuid
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
import anyio

log = logging.getLogger("orchestrator.api_runner")


def _extract_llm_meta_from_artifacts(artifacts: list[dict]) -> dict:
    """
    Cherche dans les artifacts DB un JSON contenant provider/model/latency/usage/prompts.
    On ne touche qu'aux contenus en base ; le fallback FS est géré ailleurs.
    """
    for a in artifacts:
        c = a.get("content")
        if not c:
            continue
        try:
            obj = json.loads(c)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue

        if any(
            k in obj
            for k in (
                "provider",
                "model",
                "model_used",
                "latency_ms",
                "usage",
                "prompts",
            )
        ):
            out = {
                "provider": obj.get("provider"),
                "model": obj.get("model_used") or obj.get("model"),
                "latency_ms": obj.get("latency_ms"),
                "usage": obj.get("usage"),
            }
            if obj.get("prompts") is not None:
                out["prompts"] = obj.get("prompts")
            return out
    return {}


def _normalize_llm_sidecar(data: dict) -> dict:
    """Normalise un sidecar LLM sans modifier l'original.

    - si ``model`` est absent mais ``model_used`` présent, copie la valeur
      vers ``model`` ;
    - si ``model_used`` est absent mais ``model`` présent, copie la valeur
      vers ``model_used`` ;
    - n'altère pas les autres champs ;
    - idempotent : appeler plusieurs fois ne change pas le résultat.
    """

    out = dict(data or {})
    model = out.get("model")
    model_used = out.get("model_used")

    if not model and model_used:
        out["model"] = model_used
    if not model_used and model:
        out["model_used"] = model

    return out


def _read_llm_sidecar_fs(run_id: str, node_key: str, runs_root: str = None) -> dict:
    base = runs_root or os.getenv("ARTIFACTS_DIR") or os.getenv("RUNS_ROOT") or ".runs"
    node_dir = Path(base) / run_id / "nodes" / node_key
    if not node_dir.is_dir():
        return {}
    candidates = [node_dir / f"artifact_{node_key}.llm.json"] + sorted(
        node_dir.glob("*.llm.json")
    )
    for p in candidates:
        if not p.exists():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                out = {
                    "provider": obj.get("provider"),
                    "model": obj.get("model_used") or obj.get("model"),
                    "latency_ms": obj.get("latency_ms"),
                    "usage": obj.get("usage"),
                }
                if obj.get("prompts") is not None:
                    out["prompts"] = obj.get("prompts")
                return _normalize_llm_sidecar(out)
        except Exception:
            continue
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

    if not task_spec.get("plan") and task_spec.get("type") == "demo":
        task_spec = {**task_spec, "plan": [{"id": "n1", "title": title}]}
    dag = TaskGraph.from_plan(task_spec)

    node_ids: dict[str, UUID] = {}
    node_started_at: dict[str, dt.datetime] = {}

    async def on_node_start(node, node_key: str):
        now = dt.datetime.now(dt.timezone.utc)
        node_db = await storage.save_node(
            node=Node(
                id=uuid.uuid4(),
                run_id=UUID(run_id),
                key=node_key,
                title=getattr(node, "title", "")
                or (node.get("title") if isinstance(node, dict) else ""),
                status=NodeStatus.running,
                started_at=now,
                checksum=getattr(node, "checksum", None)
                or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )
        node_ids[node_key] = node_db.id
        node_started_at[node_key] = now
        try:
            setattr(node, "db_id", node_db.id)
        except Exception:
            pass

        await event_publisher.emit(
            EventType.NODE_STARTED,
            {
                "run_id": run_id,
                "node_key": node_key,
                "checksum": getattr(node, "checksum", None),
            },
            request_id=request_id,
        )

    async def on_node_end(node, node_key: str, status: str):
        ended = dt.datetime.now(dt.timezone.utc)
        node_id = node_ids.get(node_key)
        try:
            node_status = NodeStatus(status)
        except ValueError:
            log.warning("Statut de nœud inconnu: %s", status)
            node_status = NodeStatus.failed

        await storage.save_node(
            node=Node(
                id=node_id,
                run_id=UUID(run_id),
                key=node_key,
                title=getattr(node, "title", "")
                or (node.get("title") if isinstance(node, dict) else ""),
                status=node_status,
                started_at=node_started_at.get(node_key),
                updated_at=ended,
                checksum=getattr(node, "checksum", None)
                or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )

        # ----- Enrichissement LLM: DB -> FS (+ micro‑retry) -----
        meta = {}
        node_db_id = node_id
        try:
            if node_db_id is None and hasattr(storage, "get_node_id_by_logical"):
                node_db_id = await storage.get_node_id_by_logical(run_id, node_key)
            if node_db_id and hasattr(storage, "list_artifacts_for_node"):
                artifacts = await storage.list_artifacts_for_node(node_db_id)
                meta = _extract_llm_meta_from_artifacts(artifacts) or {}
        except Exception:
            meta = {}

        if not meta:
            # micro‑retry: laisse le temps à l’exécuteur d’écrire le sidecar
            await anyio.sleep(0.35)
            meta = _read_llm_sidecar_fs(run_id, node_key) or {}

        payload = {
            "run_id": run_id,
            "node_key": node_key,
            "status": node_status.value.upper(),
            "checksum": getattr(node, "checksum", None),
        }
        if meta:
            for k in ("provider", "model", "latency_ms", "usage", "prompts"):
                v = meta.get(k)
                if v is not None:
                    payload[k] = v

        event_type = (
            EventType.NODE_COMPLETED
            if node_status == NodeStatus.completed
            else EventType.NODE_FAILED
        )
        if node_status == NodeStatus.completed:
            log.info(
                "NODE_COMPLETED run_id=%s node=%s provider=%s model=%s latency_ms=%s",
                run_id,
                node_key,
                payload.get("provider"),
                payload.get("model"),
                payload.get("latency_ms"),
            )
        await event_publisher.emit(event_type, payload, request_id=request_id)

    try:
        await event_publisher.emit(
            EventType.RUN_STARTED,
            {"run_id": run_id, "title": title},
            request_id=request_id,
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
        final_status = (
            RunStatus.completed if res.get("status") == "success" else RunStatus.failed
        )
        await storage.save_run(
            run=Run(
                id=UUID(run_id),
                title=title,
                status=final_status,
                started_at=started,
                ended_at=ended,
            )
        )
        await event_publisher.emit(
            (
                EventType.RUN_COMPLETED
                if final_status == RunStatus.completed
                else EventType.RUN_FAILED
            ),
            {"run_id": run_id},
            request_id=request_id,
        )
    except Exception as e:  # pragma: no cover
        log.exception("Background run failed for run_id=%s", run_id)
        ended = dt.datetime.now(dt.timezone.utc)
        await storage.save_run(
            run=Run(
                id=UUID(run_id),
                title=title,
                status=RunStatus.failed,
                started_at=started,
                ended_at=ended,
            )
        )
        await event_publisher.emit(
            EventType.RUN_FAILED,
            {"run_id": run_id, "error_class": e.__class__.__name__, "message": str(e)},
            request_id=request_id,
        )
