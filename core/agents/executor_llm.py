from __future__ import annotations
from textwrap import dedent
import json
import time

from core.config import resolve_llm
from core.llm.providers.base import LLMRequest, ProviderTimeout, ProviderUnavailable
from core.llm.runner import run_llm

def _build_prompts(node) -> tuple[str, str]:
    title = getattr(node, "title", node.id)
    node_type = getattr(node, "type", "task")
    acceptance = getattr(node, "acceptance", "")
    description = getattr(node, "description", "")

    system_prompt = (
        "Tu es un rédacteur technique senior. "
        "Rédige en français, clair, structuré, précis et orienté livrable. "
        "Respecte la consigne d'acceptance comme liste de critères."
    )

    user_prompt = dedent(f"""\
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
    """)
    return system_prompt, user_prompt


async def run_executor_llm(node, storage) -> bool:
    """
    Génère un artifact .md via LLM + écrit un sidecar .llm.json pour la traçabilité.
    Retourne True/False pour laisser l'orchestrateur gérer retries/recovery.
    """
    system_prompt, user_prompt = _build_prompts(node)
    provider, model, params = resolve_llm("executor")

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

        body = resp.text.strip()
        title = getattr(node, "title", node.id)
        node_type = getattr(node, "type", "task")
        acceptance = getattr(node, "acceptance", "")

        content = dedent(f"""\
        ---
        node_id: {node.id}
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
        """)

        # 1) Artifact principal (.md)
        await storage.save_artifact(node_id=node.id, content=content, ext=".md")

        # 2) Sidecar de traçabilité (.llm.json)
        trace = {
            "node_id": node.id,
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
            "prompts": {
                "system": system_prompt,
                "user": user_prompt,
            },
            "raw_hint": getattr(resp, "raw", None),
        }
        await storage.save_artifact(
            node_id=node.id,
            content=json.dumps(trace, ensure_ascii=False, indent=2),
            ext=".llm.json"
        )

        return True

    except (ProviderTimeout, ProviderUnavailable):
        return False
    except Exception:
        return False

