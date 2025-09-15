import pytest
import uuid


@pytest.mark.asyncio
async def test_get_run_unknown_returns_404(client):
    unknown = str(uuid.uuid4())
    r = await client.get(f"/runs/{unknown}", headers={"X-API-Key": "test-key"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Run not found"

