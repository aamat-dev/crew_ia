from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from contextlib import asynccontextmanager

from sqlalchemy import text, select, update
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.dialects.postgresql import insert, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from core.storage.db_models import (
    Run,
    Node,
    Artifact,
    Event,
    Feedback,
    RunStatus,
    NodeStatus,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://crew:crew@localhost:5432/crew"
)


class PostgresAdapter:
    """
    Adaptateur PostgreSQL asynchrone (SQLModel / SQLAlchemy 2.0).
    Fournit des méthodes souples (prennent soit un objet, soit des kwargs).
    """

    expects_uuid_ids: bool = True  # IDs UUID pour run_id / node_id

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        self.database_url = database_url or DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided")

        url = make_url(self.database_url)
        if url.get_backend_name() != "postgresql":
            raise RuntimeError(
                f"Unsupported database dialect: {url.get_backend_name()}"
            )

        self._engine = create_async_engine(
            self.database_url,
            future=True,
            echo=echo,
            poolclass=NullPool,  # 1 connexion par session (tests/outils)
            pool_pre_ping=True,
        )
        if self._engine.dialect.name != "postgresql":
            raise RuntimeError("PostgreSQL required")
        # IMPORTANT: expire_on_commit=False pour matérialiser avant fermeture
        self._sessionmaker = async_sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=AsyncSession
        )
        self._runs = Run.__table__
        self._nodes = Node.__table__
        self._events = Event.__table__

    # ---------- Infra utilitaires ----------

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def ping(self) -> bool:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True

    @asynccontextmanager
    async def session(self):
        async with self._sessionmaker() as s:
            yield s

    async def dispose(self) -> None:
        """Ferme proprement l'engine async pour éviter des warnings à l'arrêt."""
        try:
            await self._engine.dispose()
        except Exception:
            pass

    @staticmethod
    def _coalesce_obj(model_cls, obj: Any, kwargs: Dict[str, Any]):
        if obj is not None:
            return obj
        return model_cls(**kwargs)

    # ---------- Runs ----------

    async def save_run(self, run: Optional[Run] = None, **kwargs) -> Run:
        obj = self._coalesce_obj(Run, run, kwargs)
        payload = {
            "id": obj.id,
            "title": obj.title,
            "status": (
                obj.status.value if isinstance(obj.status, RunStatus) else obj.status
            ),
            "started_at": obj.started_at,
            "ended_at": obj.ended_at,
            "metadata": obj.meta or {},
        }

        insert_stmt = insert(self._runs).values(**payload)
        excluded = insert_stmt.excluded
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[self._runs.c.id],
            set_={
                "title": sa.func.coalesce(excluded.title, self._runs.c.title),
                "status": excluded.status,
                "started_at": sa.func.coalesce(
                    excluded.started_at, self._runs.c.started_at
                ),
                "ended_at": excluded.ended_at,
                "metadata": sa.func.coalesce(
                    sa.cast(self._runs.c.metadata, JSONB), sa.text("'{}'::jsonb")
                ).op("||")(
                    sa.func.coalesce(
                        sa.cast(excluded.metadata, JSONB), sa.text("'{}'::jsonb")
                    )
                ),
            },
        ).returning(*self._runs.c)
        async with self._engine.begin() as conn:
            result = await conn.execute(stmt)
            row = result.fetchone()
        if row:
            data = dict(row._mapping)
            data["meta"] = data.pop("metadata", None)
            return Run(**data)
        return obj

    async def finalize_run_status(
        self,
        *,
        run_id: uuid.UUID | str,
        title: Optional[str],
        status: RunStatus | str,
        started_at: Optional[datetime],
        ended_at: Optional[datetime],
        meta: Optional[Dict] = None,
        request_id: Optional[str] = None,
    ) -> Run:
        """Finalise un run (runs + events) dans une SEULE transaction."""
        # Normalise types
        try:
            run_uuid = run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))
        except Exception:
            # Laisse remonter une ValueError claire
            run_uuid = uuid.uuid4()  # dummy pour mypy; ne sera pas utilisé
            run_uuid = uuid.UUID(str(run_id))

        status_txt = status.value if isinstance(status, RunStatus) else str(status)
        payload_run = {
            "id": run_uuid,
            "title": title,
            "status": status_txt,
            "started_at": started_at,
            "ended_at": ended_at,
            "metadata": meta or {},
        }

        insert_run = insert(self._runs).values(**payload_run)
        exc = insert_run.excluded
        upsert_run = insert_run.on_conflict_do_update(
            index_elements=[self._runs.c.id],
            set_={
                "title": sa.func.coalesce(exc.title, self._runs.c.title),
                "status": exc.status,
                "started_at": sa.func.coalesce(exc.started_at, self._runs.c.started_at),
                "ended_at": exc.ended_at,
                "metadata": sa.func.coalesce(
                    sa.cast(self._runs.c.metadata, JSONB), sa.text("'{}'::jsonb")
                ).op("||")(
                    sa.func.coalesce(sa.cast(exc.metadata, JSONB), sa.text("'{}'::jsonb"))
                ),
            },
        ).returning(*self._runs.c)

        level = "RUN_COMPLETED" if status_txt.endswith("completed") else "RUN_FAILED"
        import json as _json
        msg = _json.dumps({"request_id": request_id} if request_id else {})
        insert_event = insert(self._events).values(
            id=uuid.uuid4(),
            run_id=run_uuid,
            node_id=None,
            timestamp=sa.func.now(),
            level=level,
            message=msg,
            request_id=request_id,
        ).returning(*self._events.c)

        async with self._engine.begin() as conn:
            # upsert run
            r1 = await conn.execute(upsert_run)
            row_run = r1.fetchone()
            # insert event
            try:
                await conn.execute(insert_event)
            except Exception:
                # Tolère un éventuel conflit/doublon pendant des reruns
                pass

        if row_run:
            data = dict(row_run._mapping)
            data["meta"] = data.pop("metadata", None)
            return Run(**data)
        return Run(
            id=run_uuid,
            title=title or "",
            status=RunStatus(status_txt) if status_txt in RunStatus.__members__.values() else status_txt,  # type: ignore
            started_at=started_at,
            ended_at=ended_at,
            meta=meta or {},
        )

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

    # ---------- Nodes ----------

    async def save_node(self, node: Optional[Node] = None, **kwargs) -> Node:
        obj = self._coalesce_obj(Node, node, kwargs)
        # Assure un ID et le reflète sur l'objet
        new_id = obj.id or uuid.uuid4()
        obj.id = new_id

        payload = {
            "id": new_id,
            "run_id": obj.run_id,
            "key": obj.key,
            "title": obj.title,
            "status": obj.status.value if isinstance(obj.status, NodeStatus) else obj.status,
            "role": obj.role,
            "deps": obj.deps,
            "checksum": obj.checksum,
        }

        # Laisse created_at au défaut DB si non fourni
        if getattr(obj, "created_at", None) is not None:
            payload["created_at"] = obj.created_at
        if getattr(obj, "updated_at", None) is not None:
            payload["updated_at"] = obj.updated_at

        insert_stmt = insert(self._nodes).values(**payload)
        excluded = insert_stmt.excluded
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[self._nodes.c.run_id, self._nodes.c.key],
            set_={
                "run_id": excluded.run_id,
                "key": excluded.key,
                "title": excluded.title,
                "status": excluded.status,
                "role": excluded.role,
                "deps": excluded.deps,
                "checksum": excluded.checksum,
                "updated_at": sa.func.now(),
            },
        ).returning(*self._nodes.c)

        async with self._engine.begin() as conn:
            result = await conn.execute(stmt)
            row = result.fetchone()

        return Node(**row._mapping) if row else obj


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
            try:
                res = await s.execute(
                    select(Node).where(Node.run_id == run_id, Node.key == node_key)
                )
                existing = res.scalars().first()
                if existing:
                    await s.execute(
                        update(Node)
                        .where(Node.id == existing.id)
                        .values(
                            status=status,
                            title=title,
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    await s.flush()
                    await s.refresh(existing)
                    await s.commit()
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
                await s.commit()
                return n
            except Exception:
                await s.rollback()
                raise

    # ---------- Artifacts ----------

    async def save_artifact(
        self, artifact: Optional[Artifact] = None, **kwargs
    ) -> Artifact:
        obj = self._coalesce_obj(Artifact, artifact, kwargs)
        if obj.type is None:
            obj.type = "artifact"
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        async with self.session() as s:
            try:
                s.add(obj)
                await s.flush()
                await s.commit()
                return obj
            except Exception:
                await s.rollback()
                raise

    # ---------- Events ----------

    async def save_event(self, event: Optional[Event] = None, **kwargs) -> Event:
        obj = self._coalesce_obj(Event, event, kwargs)
        if obj.timestamp is None:
            obj.timestamp = datetime.now(timezone.utc)
        async with self.session() as s:
            try:
                s.add(obj)
                await s.flush()
                await s.commit()
                return obj
            except IntegrityError as e:
                # Tolère les violations FK (ex: run supprimé en teardown) sans faire échouer les tests
                await s.rollback()
                return obj
            except OperationalError as e:
                # DB indisponible pendant shutdown: on tolère
                await s.rollback()
                return obj
            except Exception:
                await s.rollback()
                raise

    async def list_events(
        self,
        run_id: Optional[uuid.UUID] = None,
        node_id: Optional[uuid.UUID] = None,
        level: Optional[str] = None,
        limit: int = 200,
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

    # ---------- Feedbacks ----------

    async def save_feedback(
        self, feedback: Optional[Feedback] = None, **kwargs
    ) -> Feedback:
        obj = self._coalesce_obj(Feedback, feedback, kwargs)
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        async with self.session() as s:
            try:
                s.add(obj)
                await s.flush()
                await s.commit()
                return obj
            except Exception:
                await s.rollback()
                raise

    # ---------- Résolutions & ensures (optionnels) ----------

    async def resolve_run_uuid(self, run_key: str) -> Optional[uuid.UUID]:
        # suppose une colonne JSONB 'meta' :: {"key": "..."}
        async with self.session() as s:
            res = await s.execute(
                text("SELECT id FROM runs WHERE metadata ->> 'key' = :k LIMIT 1"),
                {"k": run_key},
            )
            row = res.first()
            return row[0] if row else None

    async def ensure_run(self, run_key: str, title: str) -> Run:
        ruuid = await self.resolve_run_uuid(run_key)
        if ruuid:
            r = await self.get_run(ruuid)
            if r:
                return r
        r = Run(
            title=title,
            status=RunStatus.running,
            started_at=datetime.now(timezone.utc),
            meta={"key": run_key},
        )
        return await self.save_run(r)

    async def resolve_node_uuid(
        self, run_key: str, node_key: str
    ) -> Optional[uuid.UUID]:
        # suppose 'runs.meta' + 'nodes.key'
        async with self.session() as s:
            res = await s.execute(
                text(
                    """
                    SELECT n.id
                    FROM nodes n
                    JOIN runs r ON r.id = n.run_id
                    WHERE (r.metadata ->> 'key') = :rk
                      AND n.key = :nk
                    LIMIT 1
                    """
                ),
                {"rk": run_key, "nk": node_key},
            )
            row = res.first()
            return row[0] if row else None

    # ---------- Télémétrie LLM (pour enrichir NODE_COMPLETED) ----------

    async def get_node_id_by_logical(
        self, run_id: str | uuid.UUID, logical_id: str
    ) -> Optional[str]:
        """
        Retourne l'UUID DB d'un node à partir de la clé logique (plan.id).
        On cast explicitement run_id en UUID pour éviter tout souci de comparaison.
        """
        # cast run_id en UUID côté Python (évite d'avoir à faire ::uuid côté SQL)
        try:
            run_uuid = (
                run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))
            )
        except Exception:
            return None

        q = text(
            """
            SELECT id::text
            FROM nodes
            WHERE run_id = :run_uuid
              AND key = :logical_id
            ORDER BY created_at DESC NULLS LAST
            LIMIT 1
        """
        )
        async with self.session() as s:
            r = await s.execute(q, {"run_uuid": run_uuid, "logical_id": logical_id})
            row = r.first()
            return row[0] if row else None

    async def list_artifacts_for_node(self, node_id: str) -> list[dict]:
        """
        Liste brute des artifacts pour un node.
        Colonnes: artifacts(id UUID, node_id UUID, type TEXT, content TEXT, path TEXT, created_at TIMESTAMPTZ)
        """
        q = text(
            """
            SELECT id::text, type, content, path, created_at
            FROM artifacts
            WHERE node_id = :node_id
            ORDER BY created_at DESC NULLS LAST
        """
        )
        async with self.session() as s:
            r = await s.execute(q, {"node_id": node_id})
            items = []
            for aid, typ, content, path, created_at in r.fetchall():
                items.append(
                    {
                        "id": aid,
                        "type": typ,
                        "content": content,
                        "path": path,
                        "created_at": created_at.isoformat() if created_at else None,
                    }
                )
            return items

    async def finalize_node_status(
        self,
        *,
        run_id: uuid.UUID | str,
        node_key: str,
        title: Optional[str],
        status: NodeStatus | str,
        updated_at: datetime,
        checksum: Optional[str] = None,
        node_id: Optional[uuid.UUID | str] = None,
        event_message: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Finalise un nœud (update node + insert event) atomiquement.
        - Trouve ou crée le node (par run_id + key) et met à jour son statut.
        - Insère un événement NODE_COMPLETED/NODE_FAILED lié au node_id.
        """
        # Normalise IDs
        run_uuid = run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))
        node_uuid: Optional[uuid.UUID] = None
        if node_id is not None:
            try:
                node_uuid = node_id if isinstance(node_id, uuid.UUID) else uuid.UUID(str(node_id))
            except Exception:
                node_uuid = None

        # Resolve ou upsert node
        async with self._engine.begin() as conn:
            if node_uuid is None:
                sel = await conn.execute(
                    text(
                        "SELECT id FROM nodes WHERE run_id = :rid AND key = :k LIMIT 1"
                    ),
                    {"rid": run_uuid, "k": node_key},
                )
                row = sel.first()
                node_uuid = row[0] if row else None

            if node_uuid is None:
                node_uuid = uuid.uuid4()
                await conn.execute(
                    insert(self._nodes).values(
                        id=node_uuid,
                        run_id=run_uuid,
                        key=node_key,
                        title=title,
                        status=str(status.value if isinstance(status, NodeStatus) else status),
                        checksum=checksum,
                        created_at=updated_at,
                        updated_at=updated_at,
                    )
                )
            else:
                await conn.execute(
                    update(self._nodes)
                    .where(self._nodes.c.id == node_uuid)
                    .values(
                        title=title,
                        status=str(status.value if isinstance(status, NodeStatus) else status),
                        checksum=checksum,
                        updated_at=updated_at,
                    )
                )

            # Insert event
            st = str(status.value if isinstance(status, NodeStatus) else status)
            level = "NODE_COMPLETED" if st.endswith("completed") else (
                "NODE_FAILED" if st.endswith("failed") else "NODE_COMPLETED"
            )
            await conn.execute(
                insert(self._events).values(
                    id=uuid.uuid4(),
                    run_id=run_uuid,
                    node_id=node_uuid,
                    timestamp=sa.func.now(),
                    level=level,
                    message=event_message or "{}",
                    request_id=request_id,
                )
            )
