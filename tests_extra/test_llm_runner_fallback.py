import pytest, time
from core.llm import runner

def test_fallback_provider(monkeypatch):
    called = {}
    class Dummy:
        async def __call__(self, *a, **k): return {"output":"ok"}
    monkeypatch.setattr(runner, "OllamaProvider", lambda: Dummy())
    req = runner.LLMRequest(prompt="hi", provider="ollama", model="test")
    res = pytest.run(asyncio.run(runner._provider_factory("ollama")))
