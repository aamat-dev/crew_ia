# tests/test_openai_backoff.py
import pytest
from types import SimpleNamespace

from core.llm.providers.base import LLMRequest, LLMResponse, ProviderUnavailable
from core.llm.providers import openai as openai_mod

class FakeHTTPError(Exception):
    def __init__(self, status_code, msg=""):
        self.status_code = status_code
        super().__init__(msg or f"HTTP {status_code}")

@pytest.mark.asyncio
async def test_openai_retry_then_success(monkeypatch):
    # Forcer les params de retry à petits nombres/délais
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "2")
    monkeypatch.setenv("OPENAI_BACKOFF_BASE_MS", "1")
    monkeypatch.setenv("OPENAI_BACKOFF_FACTOR", "1.0")

    # mock constructeur client (éviter besoin de vraie clé)
    class DummyClient:
        class Chat:
            class Completions:
                def create(self, *a, **k): raise RuntimeError("should not be called")
            completions = Completions()
        chat = Chat()
    def fake_ctor(self, *a, **k): return None
    # monkeypatch openai.OpenAI à un objet ayant l’API utilisée
    import builtins
    import types
    fake_openai = types.SimpleNamespace(OpenAI=lambda **kw: DummyClient())
    monkeypatch.setitem(openai_mod.__dict__, "openai", fake_openai)

    prov = openai_mod.OpenAIProvider()

    calls = {"n": 0}
    async def fake_once(req):
        calls["n"] += 1
        if calls["n"] <= 2:
            # Simule deux 429 (rate limit)
            raise FakeHTTPError(429, "Rate limit")
        return LLMResponse(text="OK")

    monkeypatch.setattr(prov, "_chat_once", fake_once)

    req = LLMRequest(system="s", prompt="p", model="gpt-4o-mini", timeout_s=5)
    out = await prov.generate(req)
    assert out.text == "OK"
    assert calls["n"] == 3  # 2 erreurs + 1 succès

@pytest.mark.asyncio
async def test_openai_retry_exhausted(monkeypatch):
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "1")
    monkeypatch.setenv("OPENAI_BACKOFF_BASE_MS", "1")
    monkeypatch.setenv("OPENAI_BACKOFF_FACTOR", "1.0")

    class DummyClient:
        class Chat:
            class Completions:
                def create(self, *a, **k): raise RuntimeError("should not be called")
            completions = Completions()
        chat = Chat()
    fake_openai = type("FakeOpenAI", (), {"OpenAI": lambda **kw: DummyClient()})
    monkeypatch.setitem(openai_mod.__dict__, "openai", fake_openai)

    prov = openai_mod.OpenAIProvider()

    class FakeHTTPError(Exception):
        def __init__(self, status_code): self.status_code = status_code

    async def fake_once(req):
        raise FakeHTTPError(500)

    monkeypatch.setattr(prov, "_chat_once", fake_once)

    req = LLMRequest(system="s", prompt="p", model="gpt-4o-mini", timeout_s=5)
    with pytest.raises(ProviderUnavailable):
        await prov.generate(req)
