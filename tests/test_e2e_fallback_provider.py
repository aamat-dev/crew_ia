# tests/test_e2e_fallback_provider.py
import json
import pytest
from types import SimpleNamespace

from core.llm.providers.base import LLMRequest, LLMResponse, ProviderUnavailable
from core.agents import executor_llm
from core.llm import runner as runner_mod
from core import config as config_mod

class DummyStorage:
    def __init__(self):
        self.writes = {}  # node_id -> {ext: content}

    async def save_artifact(self, node_id: str, content: str, ext: str = ".md"):
        self.writes.setdefault(node_id, {})[ext] = content
        return f"/tmp/{node_id}{ext}"

def fake_resolve_llm(role: str):
    # force "openai" en primaire pour le test
    return ("openai", "gpt-4o-mini", {
        "timeout_s": 10, "temperature": 0.2, "max_tokens": 256,
        "fallback_order": ["ollama", "openai"],
    })

def fake_resolve_llm_with_overrides(role: str, overrides=None):
    return fake_resolve_llm(role)

@pytest.mark.asyncio
async def test_e2e_fallback_openai_down_then_ollama_success(monkeypatch):
    """
    Cas 1: OpenAI KO -> fallback vers Ollama -> succès
    On force primary=openai via .env, et on simule:
      - OpenAIProvider.generate() -> ProviderUnavailable
      - OllamaProvider.generate() -> LLMResponse("OK")
    """
    # Config: primary openai, fallback inclut ollama
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_FALLBACK_ORDER", "ollama,openai")
    monkeypatch.setenv("LLM_TIMEOUT_S", "10")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_TOKENS", "256")
    monkeypatch.setattr(config_mod, "resolve_llm", fake_resolve_llm, raising=True)
    monkeypatch.setattr(config_mod, "resolve_llm_with_overrides", fake_resolve_llm_with_overrides, raising=True)
    # IMPORTANT: remplacer aussi les refs liées dans le module executor_llm
    monkeypatch.setattr(executor_llm, "resolve_llm", fake_resolve_llm, raising=True)
    monkeypatch.setattr(executor_llm, "resolve_llm_with_overrides", fake_resolve_llm_with_overrides, raising=True)


    # 1) OpenAI -> KO
    import types
    fake_openai_mod = __import__("core.llm.providers.openai", fromlist=["OpenAIProvider"])
    class FakeOpenAIProvider:
        async def generate(self, req: LLMRequest):
            raise ProviderUnavailable("simulated openai outage")
    monkeypatch.setattr(fake_openai_mod, "OpenAIProvider", FakeOpenAIProvider, raising=True)

    # 2) Ollama -> OK
    from core.llm.providers import ollama as ollama_mod
    async def ok_generate(self, req: LLMRequest):
        # renvoie une réponse minimale; runner complètera provider/model_used
        return LLMResponse(text="OK", raw={"message":"ok"})
    monkeypatch.setattr(ollama_mod.OllamaProvider, "generate", ok_generate, raising=True)

    # 3) Exécuter un nœud
    node = SimpleNamespace(
        id="nX", title="Etape X", type="task",
        acceptance="Une note courte", description="Rédiger une note.",
        llm={}  # pas d'override: on prend primary=openai puis fallback
    )
    storage = DummyStorage()
    ok = await executor_llm.run_executor_llm(node, storage)
    assert ok is True

    # 4) Vérifier artifacts & fallback utilisé
    assert ".md" in storage.writes["nX"]
    assert ".llm.json" in storage.writes["nX"]
    trace = json.loads(storage.writes["nX"][".llm.json"])
    assert trace["used"]["provider"] == "ollama"  # fallback effectif
    assert trace["requested"]["provider_primary"] == "openai"

@pytest.mark.asyncio
async def test_e2e_fallback_all_down_returns_false(monkeypatch):
    """
    Cas 2: OpenAI KO + Ollama KO -> l'exécuteur renvoie False (orchestrateur fera ses retries).
    """
    # Au début de test_e2e_fallback_openai_down_then_ollama_success
    # Purger tout override par rôle / legacy qui force Ollama
    for k in [
        "EXECUTOR_PROVIDER", "EXECUTOR_MODEL",
        "SUPERVISOR_PROVIDER", "SUPERVISOR_MODEL",
        "USE_OLLAMA",              # <= legacy switch
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
    ]:
        monkeypatch.delenv(k, raising=False)

    # Maintenant on pose le défaut global = openai
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_FALLBACK_ORDER", "ollama,openai")
    monkeypatch.setenv("LLM_TIMEOUT_S", "10")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_TOKENS", "256")

    # OpenAI KO
    fake_openai_mod = __import__("core.llm.providers.openai", fromlist=["OpenAIProvider"])
    class FakeOpenAIProvider:
        async def generate(self, req: LLMRequest):
            raise ProviderUnavailable("openai down")
    monkeypatch.setattr(fake_openai_mod, "OpenAIProvider", FakeOpenAIProvider, raising=True)

    # Ollama KO
    from core.llm.providers import ollama as ollama_mod
    async def ko_generate(self, req: LLMRequest):
        raise ProviderUnavailable("ollama down")
    monkeypatch.setattr(ollama_mod.OllamaProvider, "generate", ko_generate, raising=True)

    node = SimpleNamespace(id="nY", title="Etape Y", type="task",
                           acceptance="", description="")

    class DummyStorage:
        async def save_artifact(self, node_id, content, ext=".md"):
            return f"/tmp/{node_id}{ext}"

    ok = await executor_llm.run_executor_llm(node, DummyStorage())
    assert ok is False
