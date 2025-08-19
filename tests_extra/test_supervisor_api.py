import pytest, asyncio
from core.agents import supervisor

class DummyStorage:
    async def save_run(self, *a, **k): return None

@pytest.mark.asyncio
async def test_supervisor_run_basic(monkeypatch):
    async def fake_llm(*a, **k): return {"content": "ok"}
    monkeypatch.setattr("core.agents.supervisor._call_llm", fake_llm, raising=False)
    plan = await supervisor.run({"title": "T1"}, DummyStorage())
    assert hasattr(plan, "nodes")
