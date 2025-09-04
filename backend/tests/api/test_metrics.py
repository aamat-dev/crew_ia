import importlib

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager


async def _create_client_and_metrics(monkeypatch, enabled: str):
    monkeypatch.setenv("METRICS_ENABLED", enabled)
    monkeypatch.setenv("STORAGE_ORDER", "file")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test_metrics.db")

    import core.telemetry.metrics as metrics
    import backend.api.fastapi_app.deps as deps
    import backend.api.fastapi_app.middleware.metrics as mw_metrics
    import backend.api.fastapi_app.app as app_module

    importlib.reload(metrics)
    importlib.reload(deps)
    importlib.reload(mw_metrics)
    importlib.reload(app_module)

    app = app_module.app
    return app, metrics


@pytest.mark.asyncio
async def test_metrics_endpoint_enabled(monkeypatch):
    app, metrics = await _create_client_and_metrics(monkeypatch, "1")

    metrics.get_db_pool_in_use().labels(db="primary").inc()
    metrics.get_orchestrator_node_duration_seconds().labels(role="r", provider="p", model="m").observe(0.1)
    metrics.get_runs_total().labels(status="ok").inc()
    metrics.get_llm_tokens_total().labels(kind="prompt", provider="p", model="m").inc()

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # effectue une requête préalable pour générer les métriques HTTP
            await ac.get("/health")
            resp = await ac.get("/metrics")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    payload = resp.text
    for name in [
        "http_requests_total",
        "http_requests_total_family",
        "http_request_duration_seconds_bucket",
        "db_pool_in_use",
        "orchestrator_node_duration_seconds_bucket",
        "runs_total",
    ]:
        assert name in payload
    assert ("llm_tokens_total" in payload) or ("llm_cost_total" in payload)


@pytest.mark.asyncio
async def test_metrics_endpoint_disabled(monkeypatch):
    app, _ = await _create_client_and_metrics(monkeypatch, "0")

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/metrics")

    assert resp.status_code == 404
