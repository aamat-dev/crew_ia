# tests/test_config_roles_matrix.py
import importlib
import os
from typing import List
from core import config as config_mod


def _reset_env(keys: List[str]):
    for k in keys:
        os.environ.pop(k, None)


def test_manager_env_selection(monkeypatch):
    _reset_env([
        "LLM_DEFAULT_PROVIDER", "LLM_DEFAULT_MODEL",
        "MANAGER_PROVIDER", "MANAGER_MODEL",
        "LLM_TIMEOUT_S", "LLM_TEMPERATURE", "LLM_MAX_TOKENS", "LLM_FALLBACK_ORDER"
    ])

    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "llama3.1:8b")
    monkeypatch.setenv("MANAGER_PROVIDER", "openai")
    monkeypatch.setenv("MANAGER_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_FALLBACK_ORDER", "ollama,openai")
    monkeypatch.setenv("LLM_TIMEOUT_S", "60")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("LLM_MAX_TOKENS", "800")

    importlib.reload(config_mod)
    provider, model, params = config_mod.resolve_llm("manager")

    assert provider == "openai"
    assert model == "gpt-4o-mini"
    assert params["fallback_order"] == ["ollama", "openai"]


def test_recruiter_defaults_to_global_when_not_set(monkeypatch):
    keys: List[str] = [
        "LLM_DEFAULT_PROVIDER", "LLM_DEFAULT_MODEL",
        "RECRUITER_PROVIDER", "RECRUITER_MODEL"
    ]
    _reset_env(keys)

    # Neutralise toute API key susceptible d'influencer une heuristique legacy
    monkeypatch.delenv("RECRUITER_PROVIDER", raising=False)
    monkeypatch.delenv("RECRUITER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER_AUTO", raising=False)

    # Défaut explicite -> doit être honoré, sans heuristique
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "llama3.1:8b")

    # ⚠️ Empêche le rechargement du .env lors du reload du module
    monkeypatch.setenv("CONFIG_SKIP_DOTENV", "1")

    importlib.reload(config_mod)
    provider, model, _ = config_mod.resolve_llm("recruiter")

    assert provider == "ollama"
    assert model == "llama3.1:8b"
