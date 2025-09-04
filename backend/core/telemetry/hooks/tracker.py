from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional

from core.storage.db_models import NodeStatus, Event
from core.storage.postgres_adapter import PostgresAdapter
from core.storage.composite_adapter import CompositeAdapter


class DBTracker:
    """
    - Assure la création du Run (DB) à partir du run_key (lisible) et du Node (key = "n1"...).
    - Fournit des resolvers au CompositeAdapter pour traduire node_id "n1" -> UUID.
    - Écrit des Events de début/fin si souhaité.
    """

    def __init__(self, *, run_key: str, run_title: str, storage: CompositeAdapter, pg: PostgresAdapter):
        self.run_key = run_key
        self.run_title = run_title
        self.storage = storage
        self.pg = pg
        self._node_cache: Dict[str, str] = {}  # node_key -> node_uuid
        self._run_uuid: Optional[str] = None

        # branche les resolvers (utilisés par CompositeAdapter pour PG uniquement)
        self.storage.set_resolvers(
            run_resolver=self.resolve_run_uuid,
            node_resolver=self.resolve_node_uuid
        )

    # --- resolvers utilisés par CompositeAdapter -----------------------------

    async def resolve_run_uuid(self, _: str) -> Optional[str]:
        if self._run_uuid:
            return self._run_uuid
        ruuid = await self.pg.resolve_run_uuid(self.run_key)
        if ruuid:
            self._run_uuid = str(ruuid)
        return self._run_uuid

    async def resolve_node_uuid(self, node_key: str) -> Optional[str]:
        if node_key in self._node_cache:
            return self._node_cache[node_key]
        ruuid = await self.resolve_run_uuid(self.run_key)
        if not ruuid:
            return None
        nuuid = await self.pg.resolve_node_uuid(self.run_key, node_key)
        if nuuid:
            self._node_cache[node_key] = str(nuuid)
            return self._node_cache[node_key]
        return None

    # --- hooks depuis l'exécuteur -------------------------------------------

    async def on_node_start(self, node):
        # Assure run + node en DB
        run = await self.pg.ensure_run(run_key=self.run_key, title=self.run_title)
        self._run_uuid = str(run.id)

        await self.pg.ensure_node(
            run_id=run.id,
            node_key=node.id,
            title=node.title,
            status=NodeStatus.running,
            deps=node.deps or None,
            checksum=node.checksum or None,
        )
        # Event optionnel
        await self.storage.save_event(
            run_id=str(self.run_key),  # File adapter gardera un run_id lisible
            node_id=node.id,
            level="INFO",
            message=f"Node {node.id} started"
        )

    async def on_node_end(self, node, status: str):
        # Met à jour le statut du node et log un event
        ruuid = await self.resolve_run_uuid(self.run_key)
        if ruuid:
            # On laisse la MAJ fine du statut au save_node si nécessaire
            pass
        await self.storage.save_event(
            run_id=str(self.run_key),
            node_id=node.id,
            level="INFO" if status == "completed" else "ERROR",
            message=f"Node {node.id} ended with status={status}"
        )
