# core/llm/registry.py
from __future__ import annotations

from typing import Callable, Dict, Optional, Any


ProviderFactory = Callable[[], Any]


class ProviderRegistry:
    """
    Registry minimaliste pour instancier des providers par nom.
    - register(name, factory): enregistre une fabrique (sans instancier).
    - create(name): retourne une instance du provider, ou None si inconnu.
    - has(name): True/False si un nom est connu.
    - names(): liste des noms connus.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, ProviderFactory] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        key = (name or "").strip().lower()
        if not key:
            raise ValueError("Provider name cannot be empty.")
        self._factories[key] = factory

    def has(self, name: str) -> bool:
        return (name or "").strip().lower() in self._factories

    def create(self, name: str) -> Optional[Any]:
        key = (name or "").strip().lower()
        factory = self._factories.get(key)
        return factory() if factory else None

    def names(self) -> list[str]:
        return list(self._factories.keys())


# Instance globale du registry
registry = ProviderRegistry()

# Helper décorateur (facultatif) : usage @register_provider("ollama")
def register_provider(name: str):
    def _wrap(factory: ProviderFactory) -> ProviderFactory:
        registry.register(name, factory)
        return factory
    return _wrap
