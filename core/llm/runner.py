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

# NEW: registry (prioritaire) + auto-enregistrement optionnel des providers connus
from core.llm.registry import registry

# On tente d'importer les modules d'enregistrement (silencieux s'ils n'existent pas)
try:
    import core.llm.providers.ollama_registry  # noqa: F401
except Exception:
    pass
try:
    import core.llm.providers.openai_registry  # noqa: F401
except Exception:
    pass

log = logging.getLogger("crew.llm")


# ---------- LEGACY FACTORY (conservée pour compatibilité et tests) ----------
def _provider_factory(name: str):
    """
    Fabrique legacy utilisée historiquement dans la base de code et par des tests.
    Conservée telle quelle pour compatibilité.
    """
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


def _legacy_make_provider(name: str):
    """
    Expose explicitement la fabrique legacy pour les modules *._registry
    qui souhaitent la réutiliser sans dupliquer la logique.
    """
    return _provider_factory(name)


# ---------- HYBRID FACTORY (registry d'abord, legacy en fallback) ----------
def _get_provider_instance(name: str):
    """
    Tente d'abord le registry (si le provider y est enregistré),
    sinon retombe sur la fabrique legacy.
    """
    key = (name or "").strip().lower()
    if registry.has(key):
        inst = registry.create(key)
        if inst is not None:
            return inst
    # rétro-compat si non enregistré dans le registry
    return _provider_factory(key)


# ---------- Utils ----------
def _unique(seq):
    seen = set()
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            yield x


def _model_for_provider(current_provider: str, primary_provider: str, current_model: str) -> str:
    """
    Choisit le modèle à utiliser pour le provider courant.
    - Si on est sur le provider primaire, on garde le modèle demandé.
    - Sinon, on bascule sur un modèle fallback spécifique au provider.
    """
    if current_provider == primary_provider:
        return current_model
    if current_provider == "openai":
        return os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
    if current_provider == "ollama":
        return os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")
    return current_model


# ---------- Runner principal ----------
async def run_llm(req: LLMRequest, primary: Optional[str] = None, fallback_order: Optional[List[str]] = None) -> LLMResponse:
    primary = primary or req.provider or os.getenv("LLM_DEFAULT_PROVIDER", "ollama")
    order = list(_unique([primary, *(fallback_order or [])]))
    log.debug("llm.order resolved: primary=%s order=%s req.model=%s", primary, order, req.model)

    last_err: Optional[BaseException] = None

    for name in order:
        try:
            provider = _get_provider_instance(name)  # <-- registry first, legacy fallback
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
            log.warning(
                "llm.fail provider=%s model=%s err=%s",
                name,
                _model_for_provider(name, primary, req.model),
                repr(e),
            )
            continue
        except Exception as e:
            last_err = e
            log.error(
                "llm.error provider=%s model=%s err=%s",
                name,
                _model_for_provider(name, primary, req.model),
                repr(e),
            )
            continue

    log.error("llm.exhausted attempts=%s last_err=%s", order, repr(last_err))
    raise RuntimeError(f"Aucun provider n'a fonctionné (tentatives: {order}, dernier: {last_err})")
