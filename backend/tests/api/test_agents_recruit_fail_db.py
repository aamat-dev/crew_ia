import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_recruit_db_integrity_violation_returns_409(client, monkeypatch):
    async def broken_commit(self):  # type: ignore[override]
        raise IntegrityError("INSERT", {}, Exception("unique_violation"))

    monkeypatch.setattr(AsyncSession, "commit", broken_commit)

    payload = {
        "role_description": "Rédacteur/Traducteur",
        "role": "executor",
        "domain": "writer-translator",
    }

    r = await client.post(
        "/agents/recruit",
        json=payload,
        headers={"X-Request-ID": "req-recruit-fail", "X-API-Key": "test-key"},
    )
    assert r.status_code == 409, r.text
    body = r.json()
    assert body["detail"] in {"agent already exists", "conflict"}

