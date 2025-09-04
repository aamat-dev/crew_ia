# tests_api/conftest.py
import asyncio
import datetime as dt
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete, insert

# --- importe l'app et les deps ---
from api.fastapi_app.app import app
from api.fastapi_app import deps as api_deps  # <-- contient get_db et (probablement) les deps d'auth

# --- importe tes modèles & Base ---
from api.database.models import Base, Run, Node, Artifact, Event


# ---------- Engine & Session de test (SQLite fichier) ----------
# NB: on évite sqlite in-memory (connexions multiples) et on prend un fichier local de test
_TEST_DB_URL = "sqlite+aiosqlite:///./test_api.db"

engine = create_async_engine(_TEST_DB_URL, future=True, echo=False)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine():
    """
    Crée le schéma au début de la session de tests, le détruit à la fin.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """
    Fournit une session SQLAlchemy Async par test.
    """
    async with TestingSessionLocal() as session:
        yield session


# ---------- Override des deps FastAPI ----------
async def _override_get_db():
    """
    Dépendance FastAPI get_db -> renvoie une session liée à notre SQLite de test.
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
    ]
    for name in possible_auth_deps:
        dep = getattr(api_deps, name, None)
        if dep is not None:
            # remplace la dépendance par un no-op (auth OK)
            app.dependency_overrides[dep] = lambda: None


def _clear_auth_overrides():
    possible_auth_deps = [
        "get_current_user",
        "require_auth",
        "require_api_key",
        "verify_auth",
        "get_bearer_user",
        "get_api_key_user",
        "api_key_auth",
    ]
    for name in possible_auth_deps:
        dep = getattr(api_deps, name, None)
        if dep is not None and dep in app.dependency_overrides:
            del app.dependency_overrides[dep]


@pytest_asyncio.fixture
async def client(_dispose_engine) -> AsyncClient:
    """
    Client httpx avec:
      - schema DB test via override get_db
      - auth neutralisée (toutes routes accessibles)
      - gestion correcte du lifespan app (startup/shutdown)
    """
    # utilise la base de test pour les deps et l'adaptateur de stockage
    api_deps.settings.database_url = _TEST_DB_URL
    api_deps.settings.api_key = "test-key"
    # branche get_db
    app.dependency_overrides[api_deps.get_db] = _override_get_db
    app.dependency_overrides[api_deps.get_sessionmaker] = lambda: TestingSessionLocal
    # neutralise l'auth
    _disable_auth_overrides()

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    return client

@pytest_asyncio.fixture
async def client_noauth(_dispose_engine) -> AsyncClient:
    """
    Client httpx avec auth ACTIVE (pas d’override) pour tester les 401.
    Après utilisation, les overrides d'auth sont rétablis pour ne pas
    polluer les autres tests.
    """
    # utilise la base de test pour les deps et l'adaptateur de stockage
    api_deps.settings.database_url = _TEST_DB_URL
    api_deps.settings.api_key = "test-key"
    app.dependency_overrides[api_deps.get_db] = _override_get_db
    app.dependency_overrides[api_deps.get_sessionmaker] = lambda: TestingSessionLocal
    # enlève les overrides d'auth pour forcer la vraie auth
    _clear_auth_overrides()

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # réactive l'override d'auth pour les autres tests
    _disable_auth_overrides()


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
