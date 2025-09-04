import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_options_localhost(client: AsyncClient):
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization,X-API-Key,X-Request-ID",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    for method in ("GET", "POST", "PATCH", "OPTIONS"):
        assert method in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    for header in ("content-type", "authorization", "x-api-key", "x-request-id"):
        assert header in allow_headers
