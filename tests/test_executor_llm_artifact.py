# tests/test_executor_llm_artifact.py
import json
import pytest
from types import SimpleNamespace

from core.agents import executor_llm

class DummyStorage:
    def __init__(self):
        self.writes = {}  # node_id -> {ext: content}

    async def save_artifact(self, node_id: str, content: str, ext: str = ".md"):
        bucket = self.writes.setdefault(node_id, {})
        bucket[ext] = content
        # retourne un chemin fictif si besoin
        return f"/fake/{node_id}{ext}"

@pytest.mark.asyncio
async def test_executor_writes_markdown_and_llm_json(monkeypatch):
    # fake run_llm pour éviter le réseau
    class R:
        text = "OUT"
        provider = "openai"
        model_used = "gpt-4o-mini"
        raw = {"id": "fake"}
    async def fake_run_llm(req, primary, order):
        return R()

    monkeypatch.setattr(executor_llm, "run_llm", fake_run_llm)

    node = SimpleNamespace(id="nX", title="Titre", type="task",
                           acceptance="Critères...", description="Desc")
    storage = DummyStorage()

    ok = await executor_llm.run_executor_llm(node, storage)
    assert ok is True

    # vérifie l’écriture .md
    assert ".md" in storage.writes["nX"]
    md = storage.writes["nX"][".md"]
    assert "## Livrable" in md and "Titre" in md

    # vérifie l’écriture .llm.json
    assert ".llm.json" in storage.writes["nX"]
    data = json.loads(storage.writes["nX"][".llm.json"])
    assert data["used"] == {"provider": "openai", "model": "gpt-4o-mini"}
    assert "prompts" in data and "requested" in data
