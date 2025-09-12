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
from orchestrator.executor import run_graph
from core.telemetry.metrics import (
    metrics_enabled,
    get_runs_total,
    get_run_duration_seconds,
)
from orchestrator.sidecars import normalize_llm_sidecar as _normalize_llm_sidecar

import json
from pathlib import Path
import logging
import os
import anyio
import time

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
            raw_txt = p.read_text(encoding="utf-8")
            obj = json.loads(raw_txt)
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
    start_ts = time.perf_counter()
    metrics_recorded = False
    status_metric = "failed"
    # Conserve le statut/horodatage finaux pour une finalisation inconditionnelle en finally
    final_status: RunStatus | None = None
    ended: dt.datetime | None = None

    dag = TaskGraph.from_plan(task_spec)

    node_ids: dict[str, UUID] = {}
    node_started_at: dict[str, dt.datetime] = {}
    # Compteur de fin de nœuds pour finalisation anticipée du run
    nodes_total = len(dag.nodes)
    finished_count = 0
    any_failed = False
    final_event_emitted = False

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
                updated_at=now,
                checksum=getattr(node, "checksum", None)
                or (node.get("checksum") if isinstance(node, dict) else None),
            )
        )
        # Yield explicite après écriture DB critique pour éviter les courses
        await anyio.sleep(0)
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
        await anyio.sleep(0)

    async def on_node_end(node, node_key: str, status: str):
        ended = dt.datetime.now(dt.timezone.utc)
        node_id = node_ids.get(node_key)
        try:
            node_status = NodeStatus(status)
        except ValueError:
            log.warning("Statut de nœud inconnu: %s", status)
            node_status = NodeStatus.failed

        title = getattr(node, "title", "") or (node.get("title") if isinstance(node, dict) else "")

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
            await anyio.sleep(0 if os.getenv("FAST_TEST_RUN") == "1" else 0.35)
            meta = _read_llm_sidecar_fs(run_id, node_key) or {}
        duration_ms = int(
            (ended - node_started_at.get(node_key, ended)).total_seconds() * 1000
        )
        meta_payload: Dict[str, Any] = {"duration_ms": duration_ms}
        if meta:
            meta_payload.update(meta)
        # Ne pas laisser des clés conflictuelles du sidecar écraser l'identité du run/node
        meta_flat = dict(meta_payload)
        for k in ("run_id", "node_id"):
            meta_flat.pop(k, None)

        # Expose LLM metadata à la fois à la racine et dans "meta" pour la
        # rétro‑compatibilité des consommateurs d'événements.
        payload = {
            "run_id": run_id,
            "node_id": str(node_id) if node_id else None,
            "node_key": node_key,
            "status": node_status.value.upper(),
            "checksum": getattr(node, "checksum", None),
            **meta_flat,
            "meta": meta_payload,
        }
        if request_id and "request_id" not in payload:
            payload["request_id"] = request_id

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
                meta_payload.get("provider"),
                meta_payload.get("model"),
                meta_payload.get("latency_ms"),
            )
        # Finalise nœud atomiquement (update + event)
        try:
            await storage.finalize_node_status(
                run_id=run_id,
                node_key=node_key,
                title=title,
                status=node_status,
                updated_at=ended,
                checksum=getattr(node, "checksum", None)
                or (node.get("checksum") if isinstance(node, dict) else None),
                node_id=str(node_id) if node_id else None,
                event_message=json.dumps(payload),
                request_id=request_id,
            )
            # Micro‑yield immédiatement après la finalisation atomique du nœud
            await anyio.sleep(0)
        except Exception:
            # En cas d'échec, on retombe sur l’ancien chemin (tolérance)
            log.warning("finalize_node_status failed; falling back", exc_info=True)
            await storage.save_node(
                node=Node(
                    id=node_id,
                    run_id=UUID(run_id),
                    key=node_key,
                    title=title,
                    status=node_status,
                    updated_at=ended,
                    checksum=getattr(node, "checksum", None)
                    or (node.get("checksum") if isinstance(node, dict) else None),
                )
            )
            try:
                await storage.save_event(
                    run_id=run_id,
                    node_id=str(node_id) if node_id else None,
                    level=event_type.value,
                    message=json.dumps(payload),
                    request_id=request_id,
                )
            except Exception:
                pass
            # Micro‑yield juste après les deux écritures de secours
            await anyio.sleep(0)
        # Sauvegarde un petit artifact pour tests/E2E
        try:
            await storage.save_artifact(
                node_id=str(node_id) if node_id else node_key,
                content=f"# Node {node_key} completed",
            )
        except Exception:
            pass

        # ----- Finalisation anticipée du run si dernier nœud terminé -----
        nonlocal finished_count, any_failed, final_event_emitted
        if node_status in (NodeStatus.failed, NodeStatus.canceled):
            any_failed = True
        finished_count += 1
        if nodes_total and finished_count >= nodes_total and not final_event_emitted:
            # Tous les nœuds ont rendu un statut final; marque le run immédiatement (atomique si possible)
            final = RunStatus.failed if any_failed else RunStatus.completed
            try:
                await storage.finalize_run_status(
                    run_id=run_id,
                    title=title,
                    status=final,
                    started_at=started,
                    ended_at=ended,
                    meta={"request_id": request_id},
                    request_id=request_id,
                )
            except Exception:
                # En cas d'échec, la finalisation standard s'appliquera plus bas
                pass
            await anyio.sleep(0)
            final_event_emitted = True

    try:
        try:
            await event_publisher.emit(
                EventType.RUN_STARTED,
                {"run_id": run_id, "title": title},
                request_id=request_id,
            )
        except Exception:
            log.warning("run_start: emit failed", exc_info=True)
        await anyio.sleep(0)

        # Mode démo ultra-rapide (évite tout appel coûteux)
        # Ne s'applique que lorsqu'aucun plan n'est fourni.
        if (task_spec.get("type") == "demo") and not dag.nodes:
            node_key = "n1"
            await on_node_start({"title": "T1"}, node_key)
            await on_node_end({"title": "T1"}, node_key, "completed")
            res = {"status": "success"}
        else:
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
        # ...............................................................
        status_val = (res or {}).get("status")
        success_markers = {"succeeded", "success", "completed", "ok", True}
        final_status = (
            RunStatus.completed
            if status_val in success_markers
            else RunStatus.failed
        )
        status_metric = "completed" if final_status == RunStatus.completed else "failed"
        if not final_event_emitted:
            await storage.finalize_run_status(
                run_id=run_id,
                title=title,
                status=final_status,
                started_at=started,
                ended_at=ended,
                meta={"request_id": request_id},
                request_id=request_id,
            )
            # Laisse tout de suite la main pour que le polling voie l’état final
            await anyio.sleep(0)
    except Exception as e:  # pragma: no cover
        log.exception("Background run failed for run_id=%s", run_id)
        if os.getenv("SENTRY_DSN"):
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                if run_id:
                    scope.set_tag("run_id", run_id)
                sentry_sdk.capture_exception(e)
        ended = dt.datetime.now(dt.timezone.utc)
        status_metric = "failed"
        final_status = RunStatus.failed
        await storage.finalize_run_status(
            run_id=run_id,
            title=title,
            status=RunStatus.failed,
            started_at=started,
            ended_at=ended,
            meta={"request_id": request_id},
            request_id=request_id,
        )
        await anyio.sleep(0)
    finally:
        # Filet de sécurité idempotent: finalise le run même en cas de course
        if ended is not None and final_status is not None:
            try:
                await storage.finalize_run_status(
                    run_id=run_id,
                    title=title,
                    status=final_status,
                    started_at=started,
                    ended_at=ended,
                    meta={"request_id": request_id},
                    request_id=request_id,
                )
            except Exception:
                pass
            await anyio.sleep(0)
        if not metrics_recorded:
            if metrics_enabled():
                total = time.perf_counter() - start_ts
                get_runs_total().labels(status=status_metric).inc()
                get_run_duration_seconds().labels(status=status_metric).observe(total)
            metrics_recorded = True
        if os.getenv("FAST_TEST_RUN") == "1":
            # Chemin rapide en tests : on force un yield pour éviter tout blocage
            await anyio.sleep(0)
