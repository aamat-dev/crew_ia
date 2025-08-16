# tests/test_executor_llm_overrides.py
import pytest
from types import SimpleNamespace
from core.agents import executor_llm

@pytest.mark.asyncio
async def test_executor_overrides_provider_and_model(monkeypatch):
    # .env par défaut (ollama)
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "llama3.1:8b")
    monkeypatch.setenv("LLM_TIMEOUT_S", "60")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_TOKENS", "800")
    monkeypatch.setenv("LLM_FALLBACK_ORDER", "ollama,openai")

    # fake run_llm qui capture provider/model
    seen = {}
    async def fake_run_llm(req, primary, order):
        seen["provider"] = primary
        seen["model"] = req.model
        class R: text = "ok"; provider = primary; model_used = req.model; raw = {}
        return R()
    monkeypatch.setattr(executor_llm, "run_llm", fake_run_llm)

    # Node avec override LLM → OpenAI
    node = SimpleNamespace(
        id="nX",
        title="T",
        type="task",
        acceptance="",
        description="D",
        llm={"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.05, "timeout_s": 30, "max_tokens": 300}
    )

    class DummyStorage:
        async def save_artifact(self, node_id, content, ext=".md"): pass

    ok = await executor_llm.run_executor_llm(node, DummyStorage())
    assert ok is True
    assert seen["provider"] == "openai"
    assert seen["model"] == "gpt-4o-mini"
