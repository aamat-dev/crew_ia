import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_options_localhost(client: AsyncClient):
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type,X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods and "OPTIONS" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allow_headers and "x-api-key" in allow_headers
