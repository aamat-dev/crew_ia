import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_get_artifact_404(client: AsyncClient):
    resp = await client.get(f"/artifacts/{uuid.uuid4()}")
    assert resp.status_code == 404

async def test_get_artifact_ok(client: AsyncClient, seed_sample):
    # On prend un artifact existant depuis la seed via la liste des artifacts du 1er node
    node_id = seed_sample["node_ids"][0]
    lst = await client.get(f"/nodes/{node_id}/artifacts?limit=1")
    assert lst.status_code == 200
    items = lst.json().get("items", [])
    assert items, "seed should have artifacts"
    art_id = items[0]["id"]

    resp = await client.get(f"/artifacts/{art_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == art_id
    assert "content" in data  # présent dans le schema
