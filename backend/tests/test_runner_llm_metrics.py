import pytest

from core.llm.providers.base import LLMRequest, LLMResponse
from core.llm import runner
from core.telemetry.metrics import (
    get_llm_tokens_total,
    get_llm_cost_total,
)


class DummyProvider:
    async def generate(self, req):
        return LLMResponse(
            text="ok",
            raw={
                "usage": {"prompt_tokens": 3, "completion_tokens": 4},
                "cost_usd": 0.1,
            },
        )


class DummyNoUsageProvider:
    async def generate(self, req):
        return LLMResponse(text="ok")


@pytest.mark.asyncio
async def test_run_llm_metrics(monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "1")

    def fake_factory(name: str):
        return DummyProvider()

    monkeypatch.setattr(runner, "_provider_factory", fake_factory)

    tokens = get_llm_tokens_total()
    cost = get_llm_cost_total()
    tokens.labels("prompt", "dummy", "foo")._value.set(0)
    tokens.labels("completion", "dummy", "foo")._value.set(0)
    cost.labels("dummy", "foo")._value.set(0)

    req = LLMRequest(system=None, prompt="x", model="foo", provider="dummy")
    await runner.run_llm(req, primary="dummy", fallback_order=["dummy"])

    assert tokens.labels("prompt", "dummy", "foo")._value.get() == 3
    assert tokens.labels("completion", "dummy", "foo")._value.get() == 4
    assert cost.labels("dummy", "foo")._value.get() == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_run_llm_metrics_no_usage(monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "1")

    def fake_factory(name: str):
        return DummyNoUsageProvider()

    monkeypatch.setattr(runner, "_provider_factory", fake_factory)

    req = LLMRequest(system=None, prompt="x", model="bar", provider="dummy2")
    await runner.run_llm(req, primary="dummy2", fallback_order=["dummy2"])

    tokens = get_llm_tokens_total()
    samples = {
        (s.labels["kind"], s.labels["provider"], s.labels["model"]): s.value
        for s in tokens.collect()[0].samples
        if s.name == "llm_tokens_total"
    }
    assert samples.get(("prompt", "dummy2", "bar")) == 0
    assert samples.get(("completion", "dummy2", "bar")) == 0

    cost = get_llm_cost_total()
    cost_samples = {
        (s.labels["provider"], s.labels["model"]): s.value
        for s in cost.collect()[0].samples
        if s.name == "llm_cost_total"
    }
    assert ("dummy2", "bar") not in cost_samples

