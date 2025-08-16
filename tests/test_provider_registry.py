# tests/test_provider_registry.py
import pytest
from core.llm.registry import registry

class DummyProvider:
    async def generate(self, req):
        return type("Resp", (), {"text": f"dummy:{req.model}"})

def test_registry_register_and_create():
    registry.register("dummy", lambda: DummyProvider())
    inst = registry.create("dummy")
    assert inst is not None
    assert hasattr(inst, "generate")
