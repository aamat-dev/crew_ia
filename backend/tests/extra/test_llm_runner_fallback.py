import pytest
from core.llm.providers.base import LLMRequest, LLMResponse, ProviderTimeout
import core.llm.runner as runner

class FakeProvider:
    def __init__(self, name): self.name = name
    async def generate(self, req: LLMRequest) -> LLMResponse:
        if self.name == "p1":
            raise ProviderTimeout("primary timeout")
        return LLMResponse(text="ok", raw={"usage": {"input_tokens": 1}})

@pytest.mark.asyncio
async def test_runner_fallback_switch(monkeypatch):
    monkeypatch.setattr(runner, "_provider_factory", lambda name: FakeProvider(name))
    req = LLMRequest(system="sys", prompt="hi", model="m", provider="p1")
    out = await runner.run_llm(req, fallback_order=["p1","p2"])
    assert out.text == "ok"
    assert out.provider == "p2"
    assert isinstance(out.latency_ms, int)
