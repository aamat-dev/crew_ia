# core/llm/providers/base.py
from dataclasses import dataclass
from typing import Optional, Dict, List

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
class LLMResponse:
    text: str
    raw: Optional[Dict] = None
    # Ajouts pour la traçabilité
    provider: Optional[str] = None      # "ollama" | "openai" | ...
    model_used: Optional[str] = None    # modèle effectivement utilisé (peut différer en fallback)


class ProviderError(Exception): ...
class ProviderUnavailable(ProviderError): ...
class ProviderTimeout(ProviderError): ...

class LLMProvider:
    async def generate(self, req: LLMRequest) -> LLMResponse:
        raise NotImplementedError
