import pytest

@pytest.mark.asyncio
async def test_task_file_not_found_returns_400(async_client):
    r = await async_client.post(
        "/tasks",
        headers={"X-API-Key":"test-key"},
        json={"title":"Err","task_file":"does_not_exist.json"}
    )
    assert r.status_code == 400
    assert "not found" in r.json()["detail"]
