from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Tuple
from contextlib import asynccontextmanager

from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from core.storage.db_models import Run, Node, Artifact, Event, RunStatus, NodeStatus


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://crew:crew@localhost:5432/crew")


class PostgresAdapter:
    """
    Adaptateur PostgreSQL asynchrone (SQLModel / SQLAlchemy 2.0).
    Fournit des méthodes souples (prennent soit un objet, soit des kwargs).
    """
    # Indique au CompositeAdapter que cet adapter attend des UUID pour run_id / node_id
    expects_uuid_ids: bool = True

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        self.database_url = database_url or DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided")

        self._engine = create_async_engine(
            self.database_url,
            future=True,
            echo=echo,
            poolclass=NullPool,       # 1 connexion par session (évite soucis en tests / outils)
            pool_pre_ping=True,
        )
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def ping(self) -> bool:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True

    # --- Contexte de session -------------------------------------------------

    @asynccontextmanager
    async def session(self):
        """Context manager retournant une session indépendante."""
        async with self._sessionmaker() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    # --- Helpers "souples" ---------------------------------------------------

    @staticmethod
    def _coalesce_obj(model_cls, obj: Any, kwargs: Dict[str, Any]):
        if obj is not None:
            return obj
        return model_cls(**kwargs)

    # --- CRUD Run ------------------------------------------------------------

    async def save_run(self, run: Optional[Run] = None, **kwargs) -> Run:
        obj = self._coalesce_obj(Run, run, kwargs)
        async with self.session() as s:
            existing = await s.get(Run, obj.id) if obj.id else None
            if existing:
                data = obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()
                for k, v in data.items():
                    setattr(existing, k, v)
                await s.flush()
                return existing
            s.add(obj)
            await s.flush()
            return obj

    async def get_run(self, run_id: uuid.UUID) -> Optional[Run]:
        async with self.session() as s:
            return await s.get(Run, run_id)

    async def list_runs(self, limit: int = 50, offset: int = 0) -> List[Run]:
        async with self.session() as s:
            res = await s.execute(
                select(Run)
                .order_by(Run.started_at.desc().nullslast())
                .offset(offset)
                .limit(limit)
            )
            return list(res.scalars().all())

    # --- CRUD Node -----------------------------------------------------------

    async def save_node(self, node: Optional[Node] = None, **kwargs) -> Node:
        obj = self._coalesce_obj(Node, node, kwargs)
        async with self.session() as s:
            existing = await s.get(Node, obj.id) if obj.id else None
            if existing:
                data = obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()
                for k, v in data.items():
                    setattr(existing, k, v)
                await s.flush()
                return existing
            s.add(obj)
            await s.flush()
            return obj

    # --- CRUD Artifact -------------------------------------------------------

    async def save_artifact(self, artifact: Optional[Artifact] = None, **kwargs) -> Artifact:
        obj = self._coalesce_obj(Artifact, artifact, kwargs)
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        async with self.session() as s:
            s.add(obj)
            await s.flush()
            return obj

    # --- CRUD Event ----------------------------------------------------------

    async def save_event(self, event: Optional[Event] = None, **kwargs) -> Event:
        obj = self._coalesce_obj(Event, event, kwargs)
        if obj.timestamp is None:
            obj.timestamp = datetime.now(timezone.utc)
        async with self.session() as s:
            s.add(obj)
            await s.flush()
            return obj

    async def list_events(
        self,
        run_id: Optional[uuid.UUID] = None,
        node_id: Optional[uuid.UUID] = None,
        level: Optional[str] = None,
        limit: int = 200
    ) -> List[Event]:
        stmt = select(Event).order_by(Event.timestamp.desc()).limit(limit)
        if run_id:
            stmt = stmt.where(Event.run_id == run_id)
        if node_id:
            stmt = stmt.where(Event.node_id == node_id)
        if level:
            stmt = stmt.where(Event.level == level)

        async with self.session() as s:
            res = await s.execute(stmt)
            return list(res.scalars().all())

    # --- Résolutions & ensures (pour hooks / composite) ---------------------

    async def resolve_run_uuid(self, run_key: str) -> Optional[uuid.UUID]:
        """
        Trouve l'UUID du run dont metadata->>'key' == run_key
        """
        async with self.session() as s:
            res = await s.execute(
                text("SELECT id FROM runs WHERE metadata ->> 'key' = :k LIMIT 1")
                .bindparams(k=run_key)
            )
            row = res.first()
            return row[0] if row else None

    async def ensure_run(self, run_key: str, title: str) -> Run:
        ruuid = await self.resolve_run_uuid(run_key)
        if ruuid:
            r = await self.get_run(ruuid)
            if r:
                return r
        # Crée le run
        r = Run(
            title=title,
            status=RunStatus.running,
            started_at=datetime.now(timezone.utc),
            metadata={"key": run_key},
        )
        return await self.save_run(r)

    async def resolve_node_uuid(self, run_key: str, node_key: str) -> Optional[uuid.UUID]:
        """
        Sélectionne n.id via un JOIN sur runs.metadata->>'key' et nodes.key
        """
        async with self.session() as s:
            res = await s.execute(
                text("""
                    SELECT n.id
                    FROM nodes n
                    JOIN runs r ON r.id = n.run_id
                    WHERE (r.metadata ->> 'key') = :rk
                      AND n.key = :nk
                    LIMIT 1
                """).bindparams(rk=run_key, nk=node_key)
            )
            row = res.first()
            return row[0] if row else None

    async def ensure_node(
        self,
        run_id: uuid.UUID,
        node_key: str,
        title: str,
        status: NodeStatus = NodeStatus.running,
        deps: Optional[List[str]] = None,
        checksum: Optional[str] = None,
    ) -> Node:
        async with self.session() as s:
            res = await s.execute(
                select(Node).where(Node.run_id == run_id, Node.key == node_key)
            )
            existing = res.scalars().first()
            if existing:
                # mettre à jour statut / titre si besoin
                await s.execute(
                    update(Node)
                    .where(Node.id == existing.id)
                    .values(status=status, title=title, updated_at=datetime.now(timezone.utc))
                )
                await s.flush()
                return existing

            n = Node(
                run_id=run_id,
                key=node_key,
                title=title,
                status=status,
                deps=deps,
                checksum=checksum,
                created_at=datetime.now(timezone.utc),
            )
            s.add(n)
            await s.flush()
            return n
