# core/llm/providers/ollama_registry.py
from __future__ import annotations
from core.llm.registry import register_provider
from core.llm import runner  # on réutilise la fabrique legacy du runner

@register_provider("ollama")
def _ollama_factory():
    # On délègue à la fabrique legacy pour garder un code unique
    return runner._legacy_make_provider("ollama")
