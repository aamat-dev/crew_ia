# tests/test_runner_fallback_model_switch.py
import pytest
from core.llm.providers.base import LLMRequest, LLMResponse, ProviderUnavailable
from core.llm import runner

class FailProvider:
    async def generate(self, req):
        raise ProviderUnavailable("down")

class OkProvider:
    async def generate(self, req):
        return LLMResponse(text=f"provider_ok_model={req.model}")

@pytest.mark.asyncio
async def test_run_llm_switch(monkeypatch):
    monkeypatch.setenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")

    def fake_factory(name: str):
        return FailProvider() if name == "ollama" else OkProvider()
    monkeypatch.setattr(runner, "_provider_factory", fake_factory)

    req = LLMRequest(system=None, prompt="x", model="llama3.1:8b", timeout_s=5)
    res = await runner.run_llm(req, primary="ollama", fallback_order=["ollama","openai"])
    assert res.text == "provider_ok_model=gpt-4o-mini"
