"""
executor_llm.py — Exécutant "LLM"
- Produit un artifact .md structuré (front-matter + sections) à partir d'une génération LLM.
- Retourne True si tout va bien, False sinon (la reprise reste gérée par l'orchestrateur).
"""

from __future__ import annotations
from textwrap import dedent

from core.config import resolve_llm
from core.llm.providers.base import LLMRequest, ProviderTimeout, ProviderUnavailable
from core.llm.runner import run_llm


def _build_prompts(node) -> tuple[str, str]:
    """Construit (system_prompt, user_prompt) à partir des infos du nœud."""
    title = getattr(node, "title", node.id)
    node_type = getattr(node, "type", "task")
    acceptance = getattr(node, "acceptance", "")
    description = getattr(node, "description", "")

    system_prompt = (
        "Tu es un rédacteur technique senior. "
        "Rédige en français, clair, structuré, précis et orienté livrable. "
        "Respecte la consigne d'acceptance comme liste de critères."
    )

    # Le prompt utilisateur expose le contexte minimal utile
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
    Génère un artifact .md pour le nœud via LLM (provider configurable + fallback).
    """
    system_prompt, user_prompt = _build_prompts(node)

    # 1) Résoudre provider/modèle/paramètres depuis l'env
    provider, model, params = resolve_llm("executor")

    # 2) Construire la requête LLM
    req = LLMRequest(
        system=system_prompt,
        prompt=user_prompt,
        model=model,
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        timeout_s=params["timeout_s"],
    )

    try:
        # 3) Appel LLM avec fallback
        resp = await run_llm(req, provider, params["fallback_order"])
        body = resp.text.strip()

        # 4) Mise en forme type "report" (front‑matter + sections)
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

        await storage.save_artifact(node_id=node.id, content=content)
        return True

    except (ProviderTimeout, ProviderUnavailable) as e:
        # Provider HS ou timeout → on laisse l'orchestrateur décider (retries/reprise)
        # Tu peux logger ici si tu as un logger central.
        # print(f"[executor_llm] LLM indisponible: {e}")
        return False
    except Exception as e:
        # Toute autre erreur (format inattendu, etc.)
        # print(f"[executor_llm] Erreur inattendue: {e}")
        return False
