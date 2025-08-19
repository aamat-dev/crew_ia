# core/llm/providers/base.py
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
try:
    from sqlmodel import SQLModel
except Exception:  # fallback pour tests/environnements minimaux
    from pydantic import BaseModel as SQLModel


@dataclass
class LLMRequest:
    system: Optional[str]
    prompt: str
    model: str
    provider: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1500
    stop: Optional[List[str]] = None
    timeout_s: int = 60

@dataclass
class LLMResponse(SQLModel):

    """Réponse LLM normalisée. Tous les champs non essentiels sont optionnels
    pour permettre aux tests de créer des mocks minimalistes.
    """
    text: str
    provider: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: int = 0
    raw: Optional[Dict[str, Any]] = None
    usage: Dict[str, Any] = {}

class ProviderError(Exception): ...
class ProviderUnavailable(ProviderError): ...
class ProviderTimeout(ProviderError): ...

class LLMProvider:
    async def generate(self, req: LLMRequest) -> LLMResponse:
        raise NotImplementedError
