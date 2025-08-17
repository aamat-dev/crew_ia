# core/storage/db_tracking.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict

from core.storage.db_models import Run, Node, RunStatus, NodeStatus
from core.storage.postgres_adapter import PostgresAdapter


class DbTracker:
    """
    Crée le Run/Nodes en base, maintient le mapping { "n1": <uuid> },
    et expose des resolveurs compatibles CompositeAdapter.
    """

    def __init__(self, pg: PostgresAdapter, file_run_id: str, run_dir: str, title: str):
        self.pg = pg
        self.file_run_id = file_run_id
        self.run_dir = run_dir
        self.title = title
        self.run_db: Optional[Run] = None
        self.node_uuid_by_key: Dict[str, str] = {}

    # --------- création/update du RUN ----------
    async def start_run(self) -> Run:
        self.run_db = await self.pg.save_run(
            Run(
                title=self.title or "Run",
                status=RunStatus.running,
                started_at=datetime.now(timezone.utc),
                meta={"file_run_id": self.file_run_id, "run_dir": self.run_dir},
            )
        )
        return self.run_db

    async def end_run(self, success: bool) -> None:
        if not self.run_db:
            return
        await self.pg.save_run(
            Run(
                id=self.run_db.id,
                title=self.run_db.title,
                status=RunStatus.succeeded if success else RunStatus.failed,
                started_at=self.run_db.started_at,
                ended_at=datetime.now(timezone.utc),
                meta=self.run_db.meta,
            )
        )

    # --------- callbacks de nœud ----------
    async def on_node_start(self, node) -> None:
        """node.id est 'n1', 'n2'..."""
        if not self.run_db:
            raise RuntimeError("DbTracker.start_run() must be called first")
        node_db = await self.pg.save_node(
            Node(
                run_id=self.run_db.id,
                key=node.id,                 # clé logique du plan
                title=getattr(node, "title", node.id),
                status=NodeStatus.running,
                started_at=datetime.now(timezone.utc),
                deps=getattr(node, "deps", []) or [],
                checksum=getattr(node, "checksum", None),
            )
        )
        self.node_uuid_by_key[node.id] = str(node_db.id)

    async def on_node_end(self, node, success: bool) -> None:
        if not self.run_db:
            return
        node_uuid = self.node_uuid_by_key.get(node.id)
        if not node_uuid:
            return
        await self.pg.save_node(
            Node(
                id=node_uuid,
                run_id=self.run_db.id,
                key=node.id,
                title=getattr(node, "title", node.id),
                status=NodeStatus.succeeded if success else NodeStatus.failed,
                ended_at=datetime.now(timezone.utc),
            )
        )

    # --------- resolveurs pour CompositeAdapter ----------
    def resolve_run_uuid(self, maybe_key: str) -> Optional[str]:
        # on n’a qu’un run en cours : mappe l’id fichier vers l’UUID DB
        if self.run_db and maybe_key == self.file_run_id:
            return str(self.run_db.id)
        return None

    def resolve_node_uuid(self, maybe_key: str) -> Optional[str]:
        return self.node_uuid_by_key.get(maybe_key)
