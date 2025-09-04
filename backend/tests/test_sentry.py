import sys
import types
import contextlib
import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
import sentry_sdk

from api.fastapi_app.app import app
from api.fastapi_app.observability import init_sentry, SentryContextMiddleware
from orchestrator import executor
from core.planning.task_graph import PlanNode, TaskGraph


class DummyScope:
    def __init__(self):
        self.tags = {}
    def set_tag(self, key, value):
        self.tags[key] = value


@pytest.mark.anyio
async def test_sentry_capture_exception_in_api(monkeypatch):
    """Vérifie qu'une exception HTTP est capturée et taguée avec request_id."""
    monkeypatch.setenv("SENTRY_DSN", "http://foo@localhost/1")

    capture_calls = []
    tag_calls = []

    def fake_capture_exception(exc=None, *args, **kwargs):
        capture_calls.append(exc)

    def fake_set_tag(key, value=None, *args, **kwargs):
        tag_calls.append((key, value))

    monkeypatch.setattr(sentry_sdk, "capture_exception", fake_capture_exception)
    monkeypatch.setattr(sentry_sdk, "set_tag", fake_set_tag)

    @app.get("/boom")
    async def boom():  # pragma: no cover
        raise RuntimeError("boom")

    if init_sentry():
        from starlette.middleware import Middleware

        app.middleware_stack = None
        app.user_middleware.insert(0, Middleware(SentryContextMiddleware))
        app.middleware_stack = app.build_middleware_stack()

    try:
        async with LifespanManager(app):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/boom", headers={"X-Request-ID": "req-123"})
                assert resp.status_code == 500
    finally:
        # nettoyage route et middleware
        app.router.routes = [r for r in app.router.routes if r.path != "/boom"]
        app.user_middleware = [
            m for m in app.user_middleware if m.cls is not SentryContextMiddleware
        ]
        app.middleware_stack = None
        app.middleware_stack = app.build_middleware_stack()

        assert len(capture_calls) == 1


@pytest.mark.asyncio
async def test_sentry_capture_on_node_exception(monkeypatch, tmp_path):
    """Vérifie qu'une exception orchestrateur est capturée et enrichie avec run/node/provider/model."""
    monkeypatch.setenv("RUNS_ROOT", str(tmp_path))
    monkeypatch.setenv("SENTRY_DSN", "http://dummy")

    captured = []
