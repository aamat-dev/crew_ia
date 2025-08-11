# core/llm/runner.py
import os
from typing import List
from core.llm.providers.base import (
    LLMRequest, LLMResponse, ProviderTimeout, ProviderUnavailable
)
from core.llm.providers.ollama import OllamaProvider

def _provider_factory(name: str):
    name = (name or "").lower().strip()
    if name == "ollama":
        return OllamaProvider()
    if name == "openai":
        try:
            from core.llm.providers.openai import OpenAIProvider
        except Exception as e:
            raise ProviderUnavailable(f"OpenAI provider indisponible: {e}")
        return OpenAIProvider()
    raise ProviderUnavailable(f"Provider inconnu: {name}")

def _unique(seq):
    seen = set()
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            yield x

def _model_for_provider(current_provider: str, primary_provider: str, current_model: str) -> str:
    if current_provider == primary_provider:
        return current_model
    if current_provider == "openai":
        return os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
    if current_provider == "ollama":
        return os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")
    return current_model

async def run_llm(req: LLMRequest, primary: str, fallback_order: List[str]) -> LLMResponse:
    order = list(_unique([primary, *fallback_order]))
    last_err = None
    for name in order:
        try:
            provider = _provider_factory(name)
            model = _model_for_provider(name, primary, req.model)
            req_for_provider = LLMRequest(
                system=req.system,
                prompt=req.prompt,
                model=model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                stop=req.stop,
                timeout_s=req.timeout_s,
            )
            resp = await provider.generate(req_for_provider)
            # enrichir la réponse pour la traçabilité
            resp.provider = name
            resp.model_used = model
            return resp
        except (ProviderTimeout, ProviderUnavailable) as e:
            last_err = e
            continue
    raise RuntimeError(f"Aucun provider n'a fonctionné (tentatives: {order}, dernier: {last_err})")
