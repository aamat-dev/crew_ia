from __future__ import annotations
from textwrap import dedent
import json
import logging
import time
from typing import Any

from core.config import resolve_llm, resolve_llm_with_overrides
from core.llm.providers.base import LLMRequest, ProviderTimeout, ProviderUnavailable
from core.llm.runner import run_llm
from core.llm.utils import truncate

log = logging.getLogger("crew.executor")


def _json_safely(obj):
    """
    Essaie de convertir en objet JSON-sérialisable (dict/list/str/int...).
    - Si non sérialisable, on passe par json.dumps(..., default=str) puis json.loads
      pour obtenir une version "nettoyée".
    """
    if obj is None:
        return None
    try:
        json.dumps(obj)  # rapide: sérialisable tel quel ?
        return obj
    except Exception:
        try:
            txt = json.dumps(obj, ensure_ascii=False, default=str)
            return json.loads(txt)
        except Exception:
            return None


async def _safe_sidecar_write(storage, node_id: str, trace: dict) -> bool:
    """
    Tente d'écrire le sidecar .llm.json. En cas d'erreur, log et ne casse pas le nœud.
    """
    try:
        payload = json.dumps(trace, ensure_ascii=False, indent=2, default=str)
        await storage.save_artifact(node_id=node_id, content=payload, ext=".llm.json")
        return True
    except Exception as e:
        log.warning("node=%s sidecar write failed: %s", node_id, e)
        return False


def _extract_usage(raw):
    try:
        usage = raw.get("usage", None)
        if not usage:
            return None
        # OpenAI v1 renvoie un objet usage avec champs .prompt_tokens etc.
        # Quand on reçoit un SimpleNamespace-like, on convertit:
        if hasattr(usage, "__dict__"):
            usage = usage.__dict__
        return {
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
    except Exception:
        return None


def _estimate_cost(usage, provider: str, model: str) -> dict | None:
    """
    Estimation simple des coûts via .env (prix par 1K tokens).
    Variables supportées (optionnelles) :
      OPENAI_PRICE_PROMPT_$MODEL_PER_1K
      OPENAI_PRICE_COMPLETION_$MODEL_PER_1K
    Exemple :
      OPENAI_PRICE_PROMPT_GPT_4O_MINI_PER_1K=0.005
      OPENAI_PRICE_COMPLETION_GPT_4O_MINI_PER_1K=0.015
    """
    import os
    if not usage or provider != "openai":
        return None
    norm = model.upper().replace("-", "_").replace(".", "_")
    p_key = f"OPENAI_PRICE_PROMPT_{norm}_PER_1K"
    c_key = f"OPENAI_PRICE_COMPLETION_{norm}_PER_1K"
    try:
        p = float(os.getenv(p_key, "") or "0")
        c = float(os.getenv(c_key, "") or "0")
    except Exception:
        return None
    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)
    cost_prompt = (pt / 1000.0) * p
    cost_completion = (ct / 1000.0) * c
    return {
        "prompt_usd": round(cost_prompt, 6),
        "completion_usd": round(cost_completion, 6),
        "total_usd": round(cost_prompt + cost_completion, 6),
        "price_per_1k": {"prompt": p, "completion": c},
    }


def _nget(node: Any, name: str, default=""):
    """Accès tolérant: objet/dict/str (ignore les callables comme str.title)."""
    if isinstance(node, dict):
        val = node.get(name, default)
    else:
        val = getattr(node, name, default)
    return default if callable(val) else val


def _node_title(node: Any) -> str:
    t = _nget(node, "title", None)
    if t is None and isinstance(node, str):
        return node
    if not t:
        t = _nget(node, "key", "node")
    return t


def _node_id_text(node: Any) -> str:
    """ID texte robuste: utilise node.id si dispo, sinon dérive de title/key."""
    nid = _nget(node, "id", None)
    if isinstance(nid, str) and nid:
        return nid
    if nid not in (None, ""):
        try:
            return str(nid)
        except Exception:
            pass
    # fallback déterministe simple
    title = _node_title(node)
    key = _nget(node, "key", "")
    base = f"{key}|{title}".encode("utf-8", "ignore")
    import hashlib
    return f"auto-{hashlib.sha256(base).hexdigest()[:8]}"


def _build_prompts(node) -> tuple[str, str]:
    title = _node_title(node)
    node_type = _nget(node, "type", "task")
    acceptance = _nget(node, "acceptance", "")
    description = _nget(node, "description", "")

    system_prompt = (
        "Tu es un rédacteur technique senior. "
        "Rédige en français, clair, structuré, précis et orienté livrable. "
        "Respecte la consigne d'acceptance comme liste de critères."
    )

    user_prompt = dedent(
        f"""\
    Contexte:
    - Titre: {title}
    - Type: {node_type}
    - Acceptance: {acceptance or "N/A"}

    Tâche:
    {description or "Rédige une courte note structurée correspondant à la tâche."}

    Exigences:
    - Français
    - Clair et structuré (titres, sections courtes)
    - Couvrir explicitement les critères d'acceptance
    """
    )
    return system_prompt, user_prompt


async def run_executor_llm(node, storage) -> bool:
    """
    Génère un artifact .md via LLM + écrit un sidecar .llm.json pour la traçabilité.
    Retourne True/False pour laisser l'orchestrateur gérer retries/recovery.
    """
    system_prompt, user_prompt = _build_prompts(node)
    overrides = _nget(node, "llm", {}) or {}
    provider, model, params = resolve_llm_with_overrides("executor", overrides)

    node_id_txt = _node_id_text(node)

    # Log avant envoi
    log.info(
        "node=%s provider=%s model=%s timeout=%ss",
        node_id_txt,
        provider,
        model,
        params["timeout_s"],
    )

    req = LLMRequest(
        system=system_prompt,
        prompt=user_prompt,
        model=model,
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        timeout_s=params["timeout_s"],
    )

    try:
        t0 = time.monotonic()
        resp = await run_llm(req, provider, params["fallback_order"])
        dt_ms = int((time.monotonic() - t0) * 1000)

        # Log après réponse
        log.info(
            "node=%s done in %dms provider=%s model=%s",
            node_id_txt,
            dt_ms,
            getattr(resp, "provider", None),
            getattr(resp, "model_used", None),
        )

        body = resp.text.strip()
        title = _node_title(node)
        node_type = _nget(node, "type", "task")
        acceptance = _nget(node, "acceptance", "")

        usage = _extract_usage(getattr(resp, "raw", {}) or {})
        cost = _estimate_cost(usage, getattr(resp, "provider", None), getattr(resp, "model_used", None))

        # Log debug tokens & coût
        log.debug("node=%s tokens=%s cost=%s", node_id_txt, usage, cost)

        content = dedent(
            f"""\
        ---
        node_id: {node_id_txt}
        title: {title}
        type: {node_type}
        acceptance: "{(acceptance or "").replace('"','\\\"')}"
        model: {model}
        provider_primary: {provider}
        provider_fallbacks: {", ".join(params["fallback_order"])}
        ---

        # {title}

        > Type: {node_type} | Acceptation: {acceptance or "—"}

        ## Livrable
        {body}
        """
        )

        # 1) Artifact principal (.md)
        await storage.save_artifact(node_id=node_id_txt, content=content, ext=".md")

        # 2) Sidecar de traçabilité (.llm.json) — robustifié
        raw_hint_obj = _json_safely(getattr(resp, "raw", None))

        trace = {
            "node_id": node_id_txt,
            "requested": {
                "provider_primary": provider,
                "model": model,
                "fallback_order": params["fallback_order"],
                "temperature": params["temperature"],
                "max_tokens": params["max_tokens"],
                "timeout_s": params["timeout_s"],
            },
            "used": {
                "provider": getattr(resp, "provider", None),
                "model": getattr(resp, "model_used", None),
            },
            "timing_ms": dt_ms,
            "usage": usage,
            "cost_estimate": cost,
            "prompts": {
                "system": truncate(system_prompt, 2000),
                "user": truncate(user_prompt, 4000),
            },
            # 🔒 Toujours sérialisable (ou None)
            "raw_hint": raw_hint_obj,
        }

        # On ne casse PAS le nœud si le sidecar échoue à s’écrire
        await _safe_sidecar_write(storage, node_id_txt, trace)

        return True

    except (ProviderTimeout, ProviderUnavailable) as e:
        log.warning("node=%s provider error: %s", node_id_txt, e)
        return False
    except Exception as e:
        log.exception("node=%s unexpected error in executor_llm: %s", node_id_txt, e)
        return False
