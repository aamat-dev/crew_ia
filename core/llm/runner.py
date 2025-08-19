# core/llm/runner.py
from __future__ import annotations

import os
import logging
import time
from typing import List, Optional

from core.llm.providers.base import (
    LLMRequest,
    LLMResponse,
    ProviderTimeout,
    ProviderUnavailable,
)
from core.llm.providers.ollama import OllamaProvider

log = logging.getLogger("crew.llm")

def _provider_factory(name: str):
    name = (name or "").lower().strip()
    if name == "ollama":
        return OllamaProvider()
    if name == "openai":
        try:
            from core.llm.providers.openai import OpenAIProvider
        except Exception as e:
            raise ProviderUnavailable(f"OpenAI provider unavailable: {e}")
        return OpenAIProvider()
    raise ProviderUnavailable(f"Unknown provider: {name}")

def _unique(seq):
    seen = set()
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            yield x

def _model_for_provider(current_provider: str, primary_provider: str, current_model: str) -> str:
    if current_provider == primary_provider:
        return current_model
    env = f"{current_provider.upper()}_FALLBACK_MODEL"
    return os.getenv(env, current_model)

async def run_llm(req: LLMRequest, *, primary: Optional[str] = None, fallback_order: Optional[List[str]] = None) -> LLMResponse:
    order: List[str] = list(_unique(fallback_order or [primary or (req.provider or 'ollama')]))
    last_err: Exception | None = None

    for name in order:
        try:
            provider = _provider_factory(name)
            model = _model_for_provider(name, order[0], req.model)
            start = time.perf_counter()
            out = await provider.generate(LLMRequest(
                system=req.system,
                prompt=req.prompt,
                model=model,
                provider=name,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                stop=req.stop,
                timeout_s=req.timeout_s,
            ))
            dur_ms = int((time.perf_counter() - start) * 1000)
            out.provider = name
            out.model_used = model
            out.latency_ms = dur_ms
            if out.raw and isinstance(out.raw, dict):
                out.usage = out.raw.get("usage") or out.raw.get("token_usage") or out.usage
            return out
        except ProviderTimeout as e:
            last_err = e
            log.warning("llm.timeout provider=%s model=%s err=%s", name, _model_for_provider(name, order[0], req.model), repr(e))
            continue
        except ProviderUnavailable as e:
            last_err = e
            log.warning("llm.unavailable provider=%s model=%s err=%s", name, _model_for_provider(name, order[0], req.model), repr(e))
            continue
        except Exception as e:
            last_err = e
            log.error("llm.error provider=%s model=%s err=%s", name, _model_for_provider(name, order[0], req.model), repr(e))
            continue

    log.error("llm.exhausted attempts=%s last_err=%s", order, repr(last_err))
    if isinstance(last_err, ProviderTimeout):
        raise last_err
    raise ProviderUnavailable(f"All providers failed: {order}: {last_err}")
