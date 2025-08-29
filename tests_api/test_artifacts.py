import uuid
import datetime as dt
import pytest
from httpx import AsyncClient
from sqlalchemy import insert, delete
from api.database.models import Artifact

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


async def test_artifacts_ordering(client: AsyncClient, db_session, seed_sample):
    node_id = seed_sample["node_ids"][0]
    now = dt.datetime.now(dt.timezone.utc)
    extra = {
        "id": uuid.uuid4(),
        "node_id": node_id,
        "type": "markdown",
        "path": "/tmp/x.md",
        "content": "# x",
        "summary": "x",
        "created_at": now - dt.timedelta(minutes=1),
    }
    await db_session.execute(insert(Artifact), [extra])
    await db_session.commit()
    try:
        r = await client.get(f"/nodes/{node_id}/artifacts?order_by=created_at&order_dir=asc")
        items = r.json()["items"]
        dates = [it["created_at"] for it in items]
        assert dates == sorted(dates)

        r = await client.get(f"/nodes/{node_id}/artifacts?order_by=-created_at")
        items = r.json()["items"]
        dates = [it["created_at"] for it in items]
        assert dates == sorted(dates, reverse=True)

        r = await client.get(f"/nodes/{node_id}/artifacts?order_by=foo")
        assert r.status_code == 422

        r = await client.get(
            f"/nodes/{node_id}/artifacts?type=markdown&order_by=created_at&order_dir=asc&offset=1"
        )
        items = r.json()["items"]
        assert len(items) == 1
    finally:
        await db_session.execute(delete(Artifact).where(Artifact.id == extra["id"]))
        await db_session.commit()
