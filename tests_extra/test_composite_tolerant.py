import pytest, asyncio
from core.storage.composite_adapter import CompositeAdapter

class Good:
    async def get_run(self, *a, **k): return {"id": "ok"}
class Bad:
    async def get_run(self, *a, **k): raise Exception("fail")

@pytest.mark.asyncio
async def test_get_run_tolerates_errors():
    c = CompositeAdapter([Bad(), Good()])
    res = await c.get_run("x")
    assert res["id"] == "ok"
