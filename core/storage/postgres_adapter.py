# core/storage/postgres_adapter.py
from __future__ import annotations
import os
from typing import List, Optional
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from core.storage.db_models import Run, Node, Artifact, Event

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://crew:crew@localhost:5432/crew")


class PostgresAdapter:
    """Async PostgreSQL adapter (SQLModel / SQLAlchemy 2.0). No separate init() needed."""

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        self.database_url = database_url or DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided")

        # Engine async + sessionmaker prêts; NullPool pour éviter les collisions en tests
        self._engine = create_async_engine(
            self.database_url,
            future=True,
            echo=echo,
            poolclass=NullPool,     # 1 connexion par session (évite "another operation is in progress")
            pool_pre_ping=True,     # vérifie la connexion avant usage
        )
        self._sessionmaker = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @asynccontextmanager
    async def session(self):
        async with self._sessionmaker() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    # Dev helper (en prod: Alembic)
    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    # --------- CRUD ---------
    async def save_run(self, run: Run) -> Run:
        async with self.session() as s:
            db_obj = await s.get(Run, run.id) if run.id else None
            if db_obj:
                data = run.model_dump() if hasattr(run, "model_dump") else run.dict()
                for k, v in data.items():
                    setattr(db_obj, k, v)
                await s.flush()
                return db_obj
            s.add(run)
            await s.flush()
            return run

    async def get_run(self, run_id) -> Optional[Run]:
        async with self.session() as s:
            return await s.get(Run, run_id)

    async def list_runs(self, limit: int = 50, offset: int = 0) -> List[Run]:
        async with self.session() as s:
            res = await s.exec(
                select(Run)
                .order_by(Run.started_at.desc().nullslast())
                .offset(offset)
                .limit(limit)
            )
            return list(res.all())

    async def save_node(self, node: Node) -> Node:
        async with self.session() as s:
            db_obj = await s.get(Node, node.id) if node.id else None
            if db_obj:
                data = node.model_dump() if hasattr(node, "model_dump") else node.dict()
                for k, v in data.items():
                    setattr(db_obj, k, v)
                await s.flush()
                return db_obj
            s.add(node)
            await s.flush()
            return node

    async def save_artifact(self, artifact: Artifact | None = None, **kwargs) -> Artifact:
        """
        Accepte soit:
        - un objet Artifact (Artifact SQLModel), ou
        - un appel façon FileStorage: save_artifact(node_id=..., content=..., ext=".md", path=..., summary=...)
        """
        if artifact is None:
            node_id = kwargs.get("node_id")
            if node_id is None:
                raise ValueError("save_artifact: 'node_id' est requis quand 'artifact' n'est pas fourni")

            # Déduire le type à partir de l'extension si non fourni
            type_ = kwargs.get("type")
            if not type_:
                ext = kwargs.get("ext")
                if ext:
                    ext_clean = ext.lower().lstrip(".")
                    # petit mapping simple; adapte si besoin
                    mapping = {
                        "md": "markdown",
                        "txt": "text",
                        "json": "json",
                        "html": "html",
                        "png": "image",
                        "jpg": "image",
                        "jpeg": "image",
                        "pdf": "pdf",
                    }
                    type_ = mapping.get(ext_clean, ext_clean)
                else:
                    type_ = "blob"

            artifact = Artifact(
                node_id=node_id,
                type=type_,
                path=kwargs.get("path"),       # peut être None si FileStorage gère le chemin
                summary=kwargs.get("summary"),
                content=kwargs.get("content"),  # OK pour petits contenus
            )

        async with self.session() as s:
            s.add(artifact)
            await s.flush()
            return artifact

    async def save_event(self, event: Event) -> Event:
        async with self.session() as s:
            s.add(event)
            await s.flush()
            return event

    async def list_events(self, run_id=None, node_id=None, level=None, limit: int = 200):
        stmt = select(Event).order_by(Event.timestamp.desc()).limit(limit)
        if run_id:
            stmt = stmt.where(Event.run_id == run_id)
        if node_id:
            stmt = stmt.where(Event.node_id == node_id)
        if level:
            stmt = stmt.where(Event.level == level)
        async with self.session() as s:
            res = await s.exec(stmt)
            return list(res.all())

    async def ping(self) -> bool:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True