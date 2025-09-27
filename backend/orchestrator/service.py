from __future__ import annotations

import json
import uuid
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from core.planning.task_graph import TaskGraph
import anyio
from core.storage.db_models import Run, RunStatus, Node, NodeStatus
from core.storage.composite_adapter import CompositeAdapter
from orchestrator.executor import run_graph
from core.events.types import EventType


class OrchestratorService:
    """Service simple pour lancer un plan depuis ``plans.graph``."""

    def __init__(self, storage: CompositeAdapter, plans_path: str | Path | None = None):
        self.storage = storage
        self.plans_path = Path(plans_path or "plans.graph")
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()
        self._task: Optional[asyncio.Task] = None
        self._skip: Set[str] = set()
        self._overrides: Dict[str, Dict[str, Any]] = {}
        self._node_ids: Dict[str, uuid.UUID] = {}
        self.run_id: Optional[str] = None
        # timestamps pour calculer la durée des nœuds
        self._node_started_at: Dict[str, datetime] = {}

    def override(
        self,
        node_key: str,
        *,
        prompt: str | None = None,
        params: Dict[str, Any] | None = None,
    ) -> None:
        self._overrides[node_key] = {"prompt": prompt, "params": params}

    def skip(self, node_key: str) -> None:
        self._skip.add(node_key)

    async def pause(self) -> None:
        self._pause_event.clear()

    async def resume(self) -> None:
        self._pause_event.set()

    async def start(self, plan_id: str, *, dry_run: bool = False) -> str:
        data = json.loads(self.plans_path.read_text(encoding="utf-8"))
        if data.get("version") != "1.0":
            raise ValueError("plans.graph version non supportée")
        plan_spec = data.get("plans", {}).get(plan_id)
        if not plan_spec:
            raise ValueError("plan introuvable")
        dag = TaskGraph.from_plan(plan_spec)

        run_uuid = uuid.uuid4()
        self.run_id = str(run_uuid)
        now = datetime.now(timezone.utc)
        await self.storage.save_run(
            Run(
                id=run_uuid,
                title=plan_spec.get("title") or plan_id,
                status=RunStatus.running,
                started_at=now,
            )
        )
        # Publie un événement de démarrage du run pour visibilité immédiate
        try:
            await self.storage.save_event(
                run_id=run_uuid,
                level=EventType.RUN_STARTED.value,
                message=json.dumps({"run_id": str(run_uuid), "title": plan_spec.get("title") or plan_id}),
            )
            # Laisse un tick pour que l'API puisse l'observer rapidement
            await anyio.sleep(0)
        except Exception:
            pass

        for n in dag.nodes.values():
            nid = uuid.uuid4()
            self._node_ids[n.id] = nid
            await self.storage.save_node(
                Node(
                    id=nid,
                    run_id=run_uuid,
                    key=n.id,
                    title=n.title,
                    # Aligne l'état initial avec l'ENUM DB (pas de 'pending')
                    status=NodeStatus.queued,
                )
            )
            # Yield explicite après écriture DB du nœud pour éviter les courses
            await anyio.sleep(0)

        async def on_start(node, node_key):
            nid = self._node_ids.get(node_key)
            if nid:
                now_start = datetime.now(timezone.utc)
                await self.storage.save_node(
                    Node(
                        id=nid,
                        run_id=run_uuid,
                        key=node_key,
                        title=getattr(node, "title", node_key),
                        status=NodeStatus.running,
                        updated_at=now_start,
                    )
                )
                # Laisser la main juste après la mise à jour du nœud
                await anyio.sleep(0)
                # mémorise pour calculer la durée
                self._node_started_at[node_key] = now_start
                setattr(node, "db_id", str(nid))

        async def on_end(node, node_key, status):
            nid = self._node_ids.get(node_key)
            if nid:
                now_end = datetime.now(timezone.utc)
                await self.storage.save_node(
                    Node(
                        id=nid,
                        run_id=run_uuid,
                        key=node_key,
                        title=getattr(node, "title", node_key),
                        status=(
                            NodeStatus.completed
                            if status == "completed"
                            else NodeStatus.failed
                        ),
                        updated_at=now_end,
                    )
                )
                # Laisser le poller API voir l'état à jour du nœud
                await anyio.sleep(0)
                # événement NODE_COMPLETED / NODE_FAILED
                started = self._node_started_at.get(node_key)
                dur_ms = (
                    int((now_end - started).total_seconds() * 1000) if started else None
                )
                meta: Dict[str, Any] = {"duration_ms": dur_ms, "result": status}
                message = json.dumps(
                    {
                        "run_id": str(run_uuid),
                        "node_id": str(nid),
                        "node_key": node_key,
                        "meta": meta,
                    },
                    ensure_ascii=False,
                )
                level = "NODE_COMPLETED" if status == "completed" else "NODE_FAILED"
                await self.storage.save_event(
                    run_id=run_uuid,
                    node_id=nid,
                    level=level,
                    message=message,
                )

        async def _runner():
            final_status = RunStatus.failed
            signals: list[dict[str, Any]] = []
            try:
                res = await run_graph(
                    dag,
                    self.storage,
                    self.run_id,
                    dry_run=dry_run,
                    on_node_start=on_start,
                    on_node_end=on_end,
                    pause_event=self._pause_event,
                    skip_nodes=self._skip,
                    overrides=self._overrides,
                )
                signals = res.get("signals") or []
                if res.get("status") == "succeeded":
                    final_status = RunStatus.completed
            except asyncio.CancelledError:
                # Annulation explicite
                final_status = RunStatus.canceled
                raise
            except Exception:
                final_status = RunStatus.failed
                raise
            finally:
                ended = datetime.now(timezone.utc)
                meta_payload: dict[str, Any] = {}
                if signals:
                    meta_payload["signals"] = signals
                await self.storage.save_run(
                    Run(
                        id=run_uuid,
                        title=plan_spec.get("title") or plan_id,
                        status=final_status,
                        started_at=now,
                        ended_at=ended,
                        meta=meta_payload or None,
                    )
                )
                # micro‑yield post-finalisation du run
                await anyio.sleep(0)

        self._task = asyncio.create_task(_runner())
        return self.run_id

    async def wait(self) -> None:
        if self._task:
            await self._task

    async def cancel(self) -> None:
        """Annule l'exécution en cours (best effort) et marque le run en 'canceled'."""
        if self._task and not self._task.done():
            self._task.cancel()
            # Demande d'annulation; laisse un tick à l'event loop
            try:
                await anyio.sleep(0)
            except Exception:
                pass
        # Marque le run à canceled en base (au cas où le finally n'est pas passé)
        if self.run_id:
            try:
                await self.storage.save_run(
                    Run(
                        id=uuid.UUID(self.run_id),
                        title="",
                        status=RunStatus.canceled,
                        ended_at=datetime.now(timezone.utc),
                    )
                )
            except Exception:
                pass
