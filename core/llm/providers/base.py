# core/llm/providers/base.py
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

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
class LLMResponse(BaseModel):
    text: str
    provider: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None
    # 🔸 Nouveau: usage optionnel (certains providers ne l’exposent pas)
    usage: Optional[Dict[str, Any]] = None

    def ensure_usage(self):
        if self.usage is None and self.raw and isinstance(self.raw, dict):
            u = self.raw.get("usage")
            if isinstance(u, dict):
                self.usage = u
        return self

class ProviderError(Exception): ...
class ProviderUnavailable(ProviderError): ...
class ProviderTimeout(ProviderError): ...

class LLMProvider:
    async def generate(self, req: LLMRequest) -> LLMResponse:
        raise NotImplementedError
