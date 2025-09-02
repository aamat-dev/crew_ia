import pytest
from api.fastapi_app import deps
from api.fastapi_app.routes import agents as agents_routes


class DummyRecruit:
    @staticmethod
    async def recruit(session, payload, request_id):
        return {
            "agent_id": "00000000-0000-0000-0000-000000000001",
            "name": "translator-general",
            "role": "executor",
            "domain": "writer-translator",
            "default_model": "openai:gpt-4o-mini",
            "template_used": "executor-writer-translator",
            "sidecar": {"_kind": "recruitment_decision"},
        }


@pytest.mark.asyncio
async def test_recruit_endpoint_exists(client, monkeypatch):
    # RBAC ON et rôle editor
    monkeypatch.setattr(deps, "FEATURE_RBAC", True)
    monkeypatch.setattr(agents_routes, "RecruitService", DummyRecruit)
    recruit = {
        "role_description": "Traducteur EN→FR technique",
        "role": "executor",
        "domain": "writer-translator",
        "language": "fr",
    }
    r = await client.post(
        "/agents/recruit",
        json=recruit,
        headers={"X-Role": "editor", "X-Request-ID": "req-1"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["agent_id"]
    assert body["sidecar"]["_kind"] == "recruitment_decision"
