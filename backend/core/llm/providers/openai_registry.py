# core/llm/providers/openai_registry.py
from __future__ import annotations
from core.llm.registry import register_provider
from core.llm import runner  # on réutilise la fabrique legacy du runner

@register_provider("openai")
def _openai_factory():
    return runner._legacy_make_provider("openai")
