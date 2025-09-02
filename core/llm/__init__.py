from __future__ import annotations

import json
import os
from typing import Any, Dict


async def call_json(
    *,
    system: str,
    user: str,
    model: str,
    json_mode: bool = True,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Appelle OpenAI et retourne directement le JSON parsé.

    Ce helper illustre une intégration minimale avec la librairie ``openai``
    (>=1.x). Il force par défaut le mode JSON strict lorsque ``json_mode`` est
    activé.
    """

    if ":" in model:
        # Autorise les modèles de la forme ``openai:gpt-4o-mini``.
        _, model = model.split(":", 1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY manquant pour l'appel LLM")

    from openai import AsyncOpenAI  # import local pour éviter la dépendance si inutilisée

    client = AsyncOpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system or ""},
            {"role": "user", "content": user or ""},
        ],
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = await client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content if getattr(resp, "choices", None) else "{}"

    try:
        return json.loads(content or "{}")
    except json.JSONDecodeError:
        # En cas de réponse invalide, on renvoie un dict vide pour éviter de
        # propager une exception dans les hooks appelants.
        return {}
