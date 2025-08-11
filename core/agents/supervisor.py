# core/agents/supervisor.py
import json
from textwrap import dedent
from core.config import resolve_llm
from core.llm.providers.base import LLMRequest, ProviderTimeout, ProviderUnavailable
from core.llm.runner import run_llm

_SUPERVISOR_SYSTEM = dedent("""\
Tu es un planificateur d'IA. Tu analyses une tâche et produis un plan JSON STRICT :
- Clés obligatoires : "decompose" (bool), "subtasks" (liste d'objets { "title", "description" }), "plan" (liste de chaînes).
- Ne renvoie QUE du JSON, sans texte en dehors du JSON.
- Langue : français pour title/description.
- Si tu hésites, remonte des sous-tâches claires et atomiques.
""")

def _build_user_prompt(task: dict) -> str:
    title = task.get("title") or "Tâche"
    description = task.get("description") or ""
    acceptance = task.get("acceptance") or ""
    return dedent(f"""\
    Contexte:
    - Titre: {title}
    - Description: {description}
    - Acceptance (critères): {acceptance}

    Exigences de sortie (JSON strict uniquement) :
    {{
      "decompose": <true|false>,
      "subtasks": [{{"title": "…", "description": "…"}}],
      "plan": ["…", "…"]
    }}
    """)

async def run(task: dict, storage) -> dict:
    provider, model, params = resolve_llm("supervisor")
    req = LLMRequest(
        system=_SUPERVISOR_SYSTEM,
        prompt=_build_user_prompt(task),
        model=model,
        temperature=0.1,
        max_tokens=min(2000, params["max_tokens"]),
        timeout_s=params["timeout_s"],
    )
    try:
        resp = await run_llm(req, provider, params["fallback_order"])
        raw = resp.text.strip()

        # --- Traçabilité LLM (sidecar)
        trace = {
            "role": "supervisor",
            "requested": {
                "provider_primary": provider,
                "model": model,
                "fallback_order": params["fallback_order"],
                "temperature": 0.1,
                "max_tokens": min(2000, params["max_tokens"]),
                "timeout_s": params["timeout_s"],
            },
            "used": {
                "provider": getattr(resp, "provider", None),
                "model": getattr(resp, "model_used", None),
            },
            "prompts": {
                "system": _SUPERVISOR_SYSTEM,
                "user": _build_user_prompt(task),
            },
            "raw_hint": getattr(resp, "raw", None),
        }
        # on utilise un node_id symbolique pour ce sidecar
        await storage.save_artifact(node_id="supervisor", content=json.dumps(trace, ensure_ascii=False, indent=2), ext=".llm.json")

        # --- JSON strict uniquement
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Supervisor JSON invalide: objet JSON attendu.")
        for key in ("decompose", "subtasks", "plan"):
            if key not in data:
                raise ValueError(f"Supervisor JSON incomplet: clé manquante '{key}'.")
        if not isinstance(data["subtasks"], list): data["subtasks"] = []
        if not isinstance(data["plan"], list): data["plan"] = []
        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Supervisor JSON invalide: {e}; sortie={raw[:200]}")
    except (ProviderTimeout, ProviderUnavailable) as e:
        raise RuntimeError(f"Supervisor indisponible: {e}")
