import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
import sentry_sdk
from api.fastapi_app.app import app


@pytest.mark.anyio
async def test_sentry_capture_exception(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "http://example.com/42")

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

    try:
        async with LifespanManager(app):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/boom", headers={"X-Request-ID": "req-123"})
                assert resp.status_code == 500
    finally:
        app.router.routes = [r for r in app.router.routes if r.path != "/boom"]

    assert len(capture_calls) == 1
    assert ("request_id", "req-123") in tag_calls
