# tests/test_supervisor_json_strict.py
import pytest
from core.agents import supervisor

def test_build_user_prompt_contains_fields():
    p = supervisor._build_user_prompt({"title": "T", "description": "D", "acceptance": "A"})
    assert "Titre: T" in p
    assert "Description: D" in p
    assert "Acceptance (critères): A" in p

@pytest.mark.asyncio
async def test_supervisor_parsing_strict(monkeypatch):
    class DummyResp:
        text = '{"decompose": true, "subtasks":[{"title":"A","description":"B"}], "plan":["X","Y"]}'
    async def fake_run_llm(req, primary, order):
        return DummyResp()

    monkeypatch.setattr(supervisor, "run_llm", fake_run_llm)
    out = await supervisor.run({"title":"T", "description":"D"})
    assert out["decompose"] is True
    assert isinstance(out["subtasks"], list) and out["subtasks"][0]["title"] == "A"
    assert out["plan"] == ["X","Y"]
