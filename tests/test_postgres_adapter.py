import os
import pytest
import pytest_asyncio  # <-- ajoute ceci
from datetime import datetime, timezone 

from core.storage.postgres_adapter import PostgresAdapter
from core.storage.db_models import Run, Node, Artifact, Event, RunStatus, NodeStatus

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="module")
async def adapter():
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://crew:crew@localhost:5432/crew")
    a = PostgresAdapter()
    # (optionnel en dev) try/except sur create_all si tu l’appelles
    try:
        await a.create_all()
    except Exception:
        pass
    yield a

async def test_create_run_and_nodes(adapter: PostgresAdapter):
    run = Run(title="Test Run", status=RunStatus.running, started_at=datetime.now(timezone.utc))
    saved_run = await adapter.save_run(run)
    assert saved_run.id is not None

    node1 = Node(run_id=saved_run.id, title="N1", status=NodeStatus.running, deps=["n0"], checksum="abc")
    node2 = Node(run_id=saved_run.id, title="N2", status=NodeStatus.pending, deps=["n1"], checksum="def")

    await adapter.save_node(node1)
    await adapter.save_node(node2)

    got = await adapter.get_run(saved_run.id)
    assert got is not None
    runs = await adapter.list_runs(limit=10)
    assert any(r.id == saved_run.id for r in runs)

async def test_artifact_and_events(adapter: PostgresAdapter):
    run = Run(title="Artifacts Run", status=RunStatus.running, started_at=datetime.now(timezone.utc))
    await adapter.save_run(run)
    node = Node(run_id=run.id, title="Artifact Node", status=NodeStatus.running)
    await adapter.save_node(node)

    art = Artifact(node_id=node.id, type="markdown", path=".runs/x/artifact.md", content="# Hello", summary="Hello")
    saved_art = await adapter.save_artifact(art)
    assert saved_art.id is not None

    e1 = Event(run_id=run.id, node_id=node.id, level="INFO", message="Started")
    e2 = Event(run_id=run.id, node_id=node.id, level="ERROR", message="Boom")
    await adapter.save_event(e1)
    await adapter.save_event(e2)

    errors = await adapter.list_events(run_id=run.id, level="ERROR")
    assert len(errors) >= 1
