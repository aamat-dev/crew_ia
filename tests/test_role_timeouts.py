# tests/test_role_timeouts.py
import os
import pytest
from core.config import resolve_llm

def _setenv(monkeypatch, pairs):
    for k,v in pairs.items():
        monkeypatch.setenv(k, str(v))

def test_role_overrides_timeout_temp_tokens(monkeypatch):
    _setenv(monkeypatch, {
        "LLM_DEFAULT_PROVIDER": "ollama",
        "LLM_DEFAULT_MODEL": "llama3.1:8b",
        "LLM_TIMEOUT_S": "60",
        "LLM_TEMPERATURE": "0.2",
        "LLM_MAX_TOKENS": "1500",
        # overrides
        "SUPERVISOR_TIMEOUT_S": "35",
        "SUPERVISOR_TEMPERATURE": "0.05",
        "SUPERVISOR_MAX_TOKENS": "900",
        "EXECUTOR_TIMEOUT_S": "90",
        "EXECUTOR_TEMPERATURE": "0.25",
        "EXECUTOR_MAX_TOKENS": "1800",
    })

    prov_s, model_s, ps = resolve_llm("supervisor")
    prov_e, model_e, pe = resolve_llm("executor")

    assert ps["timeout_s"] == 35
    assert abs(ps["temperature"] - 0.05) < 1e-9
    assert ps["max_tokens"] == 900

    assert pe["timeout_s"] == 90
    assert abs(pe["temperature"] - 0.25) < 1e-9
    assert pe["max_tokens"] == 1800

def test_role_overrides_fallback_to_global(monkeypatch):
    # Purger toute valeur par rôle éventuellement chargée depuis .env
    for k in [
        "SUPERVISOR_TIMEOUT_S", "EXECUTOR_TIMEOUT_S",
        "SUPERVISOR_TEMPERATURE", "EXECUTOR_TEMPERATURE",
        "SUPERVISOR_MAX_TOKENS", "EXECUTOR_MAX_TOKENS",
    ]:
        monkeypatch.delenv(k, raising=False)

    # Définir uniquement les globaux
    _setenv(monkeypatch, {
        "LLM_DEFAULT_PROVIDER": "ollama",
        "LLM_DEFAULT_MODEL": "llama3.1:8b",
        "LLM_TIMEOUT_S": "70",
        "LLM_TEMPERATURE": "0.15",
        "LLM_MAX_TOKENS": "1400",
        "LLM_FALLBACK_ORDER": "ollama,openai",
    })

    _, _, ps = resolve_llm("supervisor")
    _, _, pe = resolve_llm("executor")

    assert ps["timeout_s"] == 70 and pe["timeout_s"] == 70
    assert abs(ps["temperature"] - 0.15) < 1e-9
    assert abs(pe["temperature"] - 0.15) < 1e-9
    assert ps["max_tokens"] == 1400 and pe["max_tokens"] == 1400

