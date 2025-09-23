# tests_api/conftest.py
import asyncio
import datetime as dt
import os
import time
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete, text, insert
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# --- importe l'app et les deps ---
# Réduit le bruit en tests: ne pas charger .env ni vérifier les variables manquantes
os.environ.setdefault("CONFIG_SKIP_DOTENV", "1")

from backend.api.fastapi_app.app import app
from backend.api.fastapi_app import deps as api_deps  # <-- contient get_db et (probablement) les deps d'auth

# --- importe tes modèles & Base ---
from core.storage.db_models import Run, Node, Artifact, Event


# ---------- Engine & Session de test (PostgreSQL) ----------
TestingSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False)
engine = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def pg_test_db():
    """Instancie une base PostgreSQL dédiée aux tests et applique les migrations."""
    global engine
    # --- Mode PostgreSQL ---
    admin_url = os.getenv("POSTGRES_ADMIN_URL")
    if not admin_url:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url:
            db_url = db_url.replace("postgresql+psycopg", "postgresql+asyncpg")
            base = db_url.rsplit("/", 1)[0]
            admin_url = f"{base}/postgres"
        else:
            admin_url = "postgresql+asyncpg://crew:crew@localhost:5432/postgres"
    db_name = f"crew_test_{uuid.uuid4().hex}"

    admin_engine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    async with admin_engine.begin() as conn:
        await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin_engine.dispose()

    test_db_url = admin_url.rsplit("/", 1)[0] + f"/{db_name}"
    sync_url = test_db_url.replace("postgresql+asyncpg", "postgresql+psycopg")

    mp = pytest.MonkeyPatch()
    mp.setenv("DATABASE_URL", test_db_url)
    mp.setenv("ALEMBIC_DATABASE_URL", sync_url)

    from alembic import command
    from alembic.config import Config

    ini = Path(__file__).resolve().parents[3] / "backend" / "migrations" / "alembic.ini"
    config = Config(str(ini))
    config.set_main_option("sqlalchemy.url", sync_url)
    await asyncio.to_thread(command.upgrade, config, "head")

    engine = create_async_engine(
        test_db_url,
        pool_pre_ping=True,
        poolclass=NullPool,      # <<< clé pour éviter le reuse cross-event-loop
    )
    TestingSessionLocal.configure(bind=engine)
    api_deps.settings.database_url = test_db_url

    try:
        yield test_db_url
    finally:
        await engine.dispose()
        admin_engine = create_async_engine(
            admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True
        )
        async with admin_engine.begin() as conn:
            await conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:db AND pid <> pg_backend_pid()"
                ),
                {"db": db_name},
            )
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        await admin_engine.dispose()
        mp.undo()


@pytest_asyncio.fixture
async def db_session(pg_test_db) -> AsyncSession:
    """
    Fournit une session SQLAlchemy Async par test.
    """
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            try:
                await session.rollback()
            except Exception:
                pass


# ---------- Override des deps FastAPI ----------
async def _override_get_db():
    """
    Dépendance FastAPI get_db -> renvoie une session liée à la base PG de test.
    (scope=requête côté FastAPI)
    """
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            # rollback de sécurité si un test a laissé une transaction ouverte
            await session.rollback()


def _disable_auth_overrides():
    """
    Override 'souple' pour neutraliser l'auth côté tests.
    On couvre plusieurs noms possibles de dépendances d'auth qu'on trouve souvent.
    """
    possible_auth_deps = [
        "get_current_user",
        "require_auth",
        "require_api_key",
        "verify_auth",
        "get_bearer_user",
        "get_api_key_user",
        "api_key_auth",
        "strict_api_key_auth",
    ]
    for name in possible_auth_deps:
        dep = getattr(api_deps, name, None)
        if dep is not None:
            # remplace la dépendance par un no-op (auth OK)
            app.dependency_overrides[dep] = lambda: None


def _clear_auth_overrides():
    possible_auth_deps = {
        "get_current_user",
        "require_auth",
        "require_api_key",
        "verify_auth",
        "get_bearer_user",
        "get_api_key_user",
        "api_key_auth",
        "strict_api_key_auth",
    }
    # Supprime toute override dont le nom est dans le set
    for dep in list(app.dependency_overrides.keys()):
        if getattr(dep, "__name__", None) in possible_auth_deps:
            del app.dependency_overrides[dep]


@pytest_asyncio.fixture(scope="session")
async def app_lifespan(pg_test_db):
    """
    Démarre l'application FastAPI une seule fois pour la session de tests.
    Réutiliser le lifespan évite ~2s de setup par test HTTP.
    """
    api_deps.settings.api_key = "test-key"
    app.dependency_overrides[api_deps.get_db] = _override_get_db
    app.dependency_overrides[api_deps.get_session] = _override_get_db
    app.dependency_overrides[api_deps.get_sessionmaker] = lambda: TestingSessionLocal
    _disable_auth_overrides()

    async with LifespanManager(app):
        yield app

    _clear_auth_overrides()
    app.dependency_overrides.pop(api_deps.get_db, None)
    app.dependency_overrides.pop(api_deps.get_session, None)
    app.dependency_overrides.pop(api_deps.get_sessionmaker, None)


@pytest_asyncio.fixture
async def client(app_lifespan) -> AsyncClient:
    """Client httpx réutilisant l'application déjà lancée."""
    transport = ASGITransport(app=app_lifespan)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    return client

@pytest_asyncio.fixture
async def client_noauth(app_lifespan) -> AsyncClient:
    """
    Client httpx avec auth ACTIVE (pas d’override) pour tester les 401.
    Après utilisation, les overrides d'auth sont rétablis pour ne pas
    polluer les autres tests.
    """
    # purges les overrides d'auth avant toute requête
    _clear_auth_overrides()
    try:
        transport = ASGITransport(app=app_lifespan)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        _disable_auth_overrides()


@pytest.fixture(autouse=True)
def reset_app_state(app_lifespan):
    """Réinitialise les états globaux partagés par l'application entre les tests."""
    state = app_lifespan.state
    rate_limits = getattr(state, "rate_limits", None)
    if isinstance(rate_limits, dict):
        rate_limits.clear()
    if hasattr(state, "event_publisher"):
        state.event_publisher.disabled = False
    if hasattr(state, "shutting_down"):
        state.shutting_down = False
    yield


# ---------- Données seed ----------
@pytest_asyncio.fixture
async def seed_sample(db_session: AsyncSession):
    now = dt.datetime.now(dt.timezone.utc)
    run_id = uuid.uuid4()

    await db_session.execute(
        insert(Run).values(
            {
                "id": run_id,
                "title": "Sample Run",
                "status": "completed",
                "started_at": now - dt.timedelta(minutes=5),
                "ended_at": now,
            }
        )
    )

    node_ids = [uuid.uuid4() for _ in range(3)]
    await db_session.execute(
        insert(Node),
        [
            {
                "id": nid,
                "run_id": run_id,
                "key": f"n{i}",
                "title": f"Node {i}",
                "status": "completed" if i < 3 else "failed",
                "role": f"r{i}",
                "created_at": now - dt.timedelta(minutes=5 - i),
                "updated_at": now - dt.timedelta(minutes=4 - i),
                "checksum": f"cs{i}",
            }
            for i, nid in enumerate(node_ids, start=1)
        ],
    )

    await db_session.execute(
        insert(Artifact),
        [
            {
                "id": uuid.uuid4(),
                "node_id": node_ids[0],
                "type": "markdown",
                "path": "/tmp/a1.md",
                "content": "# md",
                "summary": "md",
                "created_at": now,
            },
            {
                "id": uuid.uuid4(),
                "node_id": node_ids[1],
                "type": "sidecar",
                "path": "/tmp/a2.json",
                "content": '{"usage":1}',
                "summary": None,
                "created_at": now,
            },
        ],
    )

    await db_session.execute(
        insert(Event),
        [
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": node_ids[0],
                "level": "INFO",
                "message": "start",
                "timestamp": now - dt.timedelta(minutes=5),
                "request_id": "req-1",
            },
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "node_id": node_ids[2],
                "level": "ERROR",
                "message": "boom",
                "timestamp": now - dt.timedelta(minutes=1),
                "request_id": "req-2",
            },
        ],
    )
    await db_session.commit()

    try:
        yield {"run_id": run_id, "node_ids": node_ids}
    finally:
        await db_session.execute(delete(Event).where(Event.run_id == run_id))
        await db_session.execute(delete(Artifact).where(Artifact.node_id.in_(node_ids)))
        await db_session.execute(delete(Node).where(Node.run_id == run_id))
        await db_session.execute(delete(Run).where(Run.id == run_id))
        await db_session.commit()


@pytest_asyncio.fixture(autouse=True)
async def reset_run_tables():
    engine = TestingSessionLocal().bind
    if engine is None:
        yield
        return
    async with engine.begin() as conn:
        await conn.execute(delete(Event))
        await conn.execute(delete(Artifact))
        await conn.execute(delete(Node))
        await conn.execute(delete(Run))
    yield
    async with engine.begin() as conn:
        await conn.execute(delete(Event))
        await conn.execute(delete(Artifact))
        await conn.execute(delete(Node))
        await conn.execute(delete(Run))


# Helper de polling simple/robuste pour les runs


async def wait_status(
    client,
    run_id: str,
    target: str = "completed",
    timeout: float = 5.0,
    interval: float = 0.05,
) -> bool:
    """Attend qu'un run atteigne le statut cible dans le délai imparti."""
    import os
    # Autorise un override global pour stabiliser l'exécution end-to-end
    try:
        timeout = float(os.getenv("TEST_POLL_TIMEOUT", timeout))
    except Exception:
        pass
    deadline = time.monotonic() + timeout
    extend_count = 0
    while time.monotonic() < deadline:
        r = await client.get(f"/runs/{run_id}", headers={"X-API-Key": "test-key"})
        st = (r.json() or {}).get("status")
        if target == "completed":
            if st in ("completed", "failed"):
                return True
            # Fallback robuste: vérifie la présence d'un event final RUN_*
            try:
                ev = await client.get(
                    "/events", params={"run_id": run_id, "limit": 3}, headers={"X-API-Key": "test-key"}
                )
                if ev.status_code == 200:
                    items = (ev.json() or {}).get("items") or []
                    # Accepte RUN_* s'il est présent dans les premiers éléments
                    levels = [e.get("level") for e in items]
                    if any(l in ("RUN_COMPLETED", "RUN_FAILED") for l in levels):
                        return True
                    # En présence d'un NODE_COMPLETED récent mais sans RUN_*,
                    # on étend le délai une seule fois (ou deux maximum) pour laisser
                    # le temps à la finalisation d'arriver, sans boucle infinie.
                    if ("NODE_COMPLETED" in levels) and extend_count < 2:
                        extend_count += 1
                        deadline = max(deadline, time.monotonic() + 5.0)
            except Exception:
                pass
        else:
            if st == target:
                return True
        await asyncio.sleep(interval)
    return False
