import uuid
import pytest

from core.storage.postgres_adapter import PostgresAdapter
from core.storage.db_models import Run, RunStatus
from backend.tests.api.conftest import pg_test_db


@pytest.mark.asyncio
async def test_save_run_returns_model_with_meta(pg_test_db):
    adapter = PostgresAdapter(pg_test_db)
    run = Run(id=uuid.uuid4(), title="T", status=RunStatus.running, meta={"k": "v"})
    saved = await adapter.save_run(run)
    assert isinstance(saved, Run)
    assert saved.meta == {"k": "v"}
