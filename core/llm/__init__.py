from __future__ import annotations
from typing import Any, Dict

async def call_json(*, system: str, user: str, model: str, json_mode: bool = True, temperature: float = 0.0) -> Dict[str, Any]:
    """Appelle un LLM et retourne du JSON parsé.
    À implémenter selon ton fournisseur d'inférence."""
    raise NotImplementedError("Implement core.llm.call_json for your inference provider.")
