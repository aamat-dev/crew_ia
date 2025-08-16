# tests/test_manager_fallback_chain.py
import importlib
import pytest

from core.llm.providers.base import LLMRequest, LLMResponse, ProviderUnavailable
from core.llm import runner
from core import config as config_mod


class FailProvider:
    async def generate(self, req):
        raise ProviderUnavailable("down")


class OkProvider:
    async def generate(self, req):
        return LLMResponse(text=f"ok:{req.model}")


@pytest.mark.asyncio
async def test_manager_env_plus_fallback(monkeypatch):
    # Manager configuré sur ollama, mais ollama tombe → fallback openai
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "llama3.1:8b")
    monkeypatch.setenv("MANAGER_PROVIDER", "ollama")
    monkeypatch.setenv("MANAGER_MODEL", "llama3.1:8b")
    monkeypatch.setenv("LLM_FALLBACK_ORDER", "ollama,openai")
    monkeypatch.setenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
    monkeypatch.delenv("RECRUITER_PROVIDER", raising=False)
    monkeypatch.delenv("RECRUITER_MODEL", raising=False)

    importlib.reload(config_mod)
    provider, model, params = config_mod.resolve_llm("manager")
    assert provider == "ollama" and model == "llama3.1:8b"

    # Simule : ollama down, openai ok
    def fake_factory(name: str):
        return FailProvider() if name == "ollama" else OkProvider()

    monkeypatch.setattr(runner, "_provider_factory", fake_factory)

    req = LLMRequest(system=None, prompt="hello", model=model, timeout_s=5)
    res = await runner.run_llm(req, primary=provider, fallback_order=params["fallback_order"])
    assert res.text == "ok:gpt-4o-mini"
