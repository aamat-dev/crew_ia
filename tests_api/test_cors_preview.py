import importlib

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager


@pytest.mark.asyncio
async def test_cors_preview(monkeypatch):
    origin = "https://org-project-123.vercel.app"
    other_origin = "https://user.github.io"
    import os
    original = os.getenv("ALLOWED_ORIGINS")
    monkeypatch.setenv("ALLOWED_ORIGINS", f"{origin},{other_origin}")

    import api.fastapi_app.app as app_module
    importlib.reload(app_module)
    app = app_module.app

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.options(
                "/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type,X-API-Key",
                },
            )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods and "OPTIONS" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allow_headers and "x-api-key" in allow_headers

    if original is not None:
        monkeypatch.setenv("ALLOWED_ORIGINS", original)
    else:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    importlib.reload(app_module)
