# core/llm/runner.py
import os
import logging
import time
from typing import List
from core.llm.providers.base import (
    LLMRequest, LLMResponse, ProviderTimeout, ProviderUnavailable
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
    log.debug("llm.order resolved: primary=%s order=%s req.model=%s", primary, order, req.model)

    last_err = None
    for name in order:
        try:
            provider = _provider_factory(name)
            model = _model_for_provider(name, primary, req.model)

            log.info("llm.call provider=%s model=%s timeout=%ss", name, model, req.timeout_s)

            t0 = time.monotonic()
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
            dt_ms = int((time.monotonic() - t0) * 1000)

            # enrichir la réponse pour la traçabilité
            resp.provider = name
            resp.model_used = model

            log.info("llm.used provider=%s model=%s duration_ms=%d", name, model, dt_ms)
            return resp

        except (ProviderTimeout, ProviderUnavailable) as e:
            last_err = e
            log.warning("llm.fail provider=%s model=%s err=%s", name, _model_for_provider(name, primary, req.model), repr(e))
            continue
        except Exception as e:
            last_err = e
            log.error("llm.error provider=%s model=%s err=%s", name, _model_for_provider(name, primary, req.model), repr(e))
            continue

    log.error("llm.exhausted attempts=%s last_err=%s", order, repr(last_err))
    raise RuntimeError(f"Aucun provider n'a fonctionné (tentatives: {order}, dernier: {last_err})")
