# tests/test_supervisor_json_strict.py
import pytest
from core.agents import supervisor

@pytest.mark.asyncio
async def test_supervisor_parsing_strict(monkeypatch):
    # Fake run_llm (pas d'appel réseau)
    class DummyResp:
        text = '{"decompose": true, "subtasks":[{"title":"A","description":"B"}], "plan":["X","Y"]}'
    async def fake_run_llm(req, primary, order):
        return DummyResp()

    monkeypatch.setattr(supervisor, "run_llm", fake_run_llm)

    # Storage factice pour supporter l'écriture du sidecar .llm.json
    class DummyStorage:
        def __init__(self): self.saved = []
        async def save_artifact(self, node_id: str, content: str, ext: str = ".md"):
            self.saved.append((node_id, ext, content))
            return f"/tmp/{node_id}{ext}"

    storage = DummyStorage()

    out = await supervisor.run({"title":"T", "description":"D"}, storage)

    assert out["decompose"] is True
    assert isinstance(out["subtasks"], list) and out["subtasks"][0]["title"] == "A"
    assert out["plan"] == ["X","Y"]

    # Vérifie qu'un sidecar superviseur a été écrit
    assert any(e[0] == "supervisor" and e[1] == ".llm.json" for e in storage.saved)
