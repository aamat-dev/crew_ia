import sys
from pathlib import Path
import pytest
import sqlalchemy as sa

try:
    from tests.api.conftest import *  # noqa: F401,F403
except ImportError:  # pragma: no cover - fallback when package not on path
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tests.api.conftest import *  # noqa: F401,F403


def reset_settings_env(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import backend.api.fastapi_app.deps as deps
    deps.get_settings.cache_clear()
    deps.settings = deps.get_settings()


@pytest.fixture(autouse=True)
async def _empty_matrix(db_session):
    await db_session.execute(sa.text("DELETE FROM agent_models_matrix"))
    await db_session.commit()
    yield


@pytest.fixture(autouse=True)
def env_fast_test(monkeypatch):
    """Force le mode FAST_TEST_RUN pour raccourcir les délais."""
    monkeypatch.setenv("FAST_TEST_RUN", "1")
    # Allonge légèrement le délai de polling quand la suite complète tourne
    monkeypatch.setenv("TEST_POLL_TIMEOUT", "10.0")
    # Simplifie le backend de stockage en tests pour éviter la variabilité
    monkeypatch.setenv("STORAGE_ORDER", "pg")
    yield


@pytest.fixture
def artifacts_tmpdir(tmp_path, monkeypatch):
    """Isole les artifacts dans un répertoire temporaire."""
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("ARTIFACTS_DIR", str(runs_dir))
    yield runs_dir
