import pytest


@pytest.mark.asyncio
async def test_cors_disallowed_origin_has_no_cors_headers(client):
    # Origin non autorisée -> pas d'en-têtes CORS ajoutés
    r = await client.get("/runs", headers={"Origin": "https://evil.example", "X-API-Key": "test-key"})
    assert r.status_code == 200
    # Starlette CORS ne renvoie pas 403, il omet les headers "Access-Control-Allow-*"
    assert "access-control-allow-origin" not in {k.lower(): v for k, v in r.headers.items()}


@pytest.mark.asyncio
async def test_cors_allowed_origin_headers_present(client, monkeypatch):
    # Origin autorisée par défaut via settings.allowed_origins (localhost:3000)
    origin = "http://localhost:3000"
    r = await client.get("/runs", headers={"Origin": origin, "X-API-Key": "test-key"})
    assert r.status_code == 200
    headers = {k.lower(): v for k, v in r.headers.items()}
    assert headers.get("access-control-allow-origin") == origin
    # Vary doit inclure Origin pour caches
    vary = headers.get("vary", "")
    assert "origin" in vary.lower()

