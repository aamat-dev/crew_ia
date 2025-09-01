from __future__ import annotations

import json
import uuid
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from core.planning.task_graph import TaskGraph
from core.storage.db_models import Run, RunStatus, Node, NodeStatus
from core.storage.composite_adapter import CompositeAdapter
from apps.orchestrator.executor import run_graph


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

    def override(self, node_key: str, *, prompt: str | None = None, params: Dict[str, Any] | None = None) -> None:
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
            Run(id=run_uuid, title=plan_spec.get("title") or plan_id, status=RunStatus.running, started_at=now)
        )

        for n in dag.nodes.values():
            nid = uuid.uuid4()
            self._node_ids[n.id] = nid
            await self.storage.save_node(
                Node(id=nid, run_id=run_uuid, key=n.id, title=n.title, status=NodeStatus.pending)
            )

        async def on_start(node, node_key):
            nid = self._node_ids.get(node_key)
            if nid:
                await self.storage.save_node(
                    Node(id=nid, run_id=run_uuid, key=node_key, title=getattr(node, "title", node_key), status=NodeStatus.running, started_at=datetime.now(timezone.utc))
                )
                setattr(node, "db_id", str(nid))

        async def on_end(node, node_key, status):
            nid = self._node_ids.get(node_key)
            if nid:
                await self.storage.save_node(
                    Node(id=nid, run_id=run_uuid, key=node_key, title=getattr(node, "title", node_key), status=NodeStatus.completed if status=="completed" else NodeStatus.failed, updated_at=datetime.now(timezone.utc))
                )

        self._task = asyncio.create_task(
            run_graph(
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
        )
        return self.run_id

    async def wait(self) -> None:
        if self._task:
            await self._task
