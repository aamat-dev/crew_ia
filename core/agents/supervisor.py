# core/agents/supervisor.py
import json
import logging

from textwrap import dedent
from core.config import resolve_llm
from core.llm.providers.base import LLMRequest, ProviderTimeout, ProviderUnavailable
from core.llm.runner import run_llm
from core.llm.utils import truncate

_SUPERVISOR_SYSTEM = dedent("""\
Tu es un planificateur d'IA. Tu analyses une tâche et produis un plan JSON STRICT :
- Clés obligatoires : "decompose" (bool), "subtasks" (liste d'objets { "title", "description" }), "plan" (liste de chaînes).
- Ne renvoie QUE du JSON, sans texte en dehors du JSON.
- Langue : français pour title/description.
- Si tu hésites, remonte des sous-tâches claires et atomiques.
""")

log = logging.getLogger("crew.supervisor")

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

    # Log avant l'appel au LLM
    log.info(
        "supervisor call: provider=%s model=%s timeout=%ss",
        provider, model, params["timeout_s"]
    )

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

        # Log après l'appel au LLM
        log.info(
            "supervisor used: provider=%s model=%s",
            getattr(resp, "provider", None),
            getattr(resp, "model_used", None),
        )

        usage = None
        cost = None
        if getattr(resp, "provider", None) == "openai":
            _raw = getattr(resp, "raw", {}) or {}
            try:
                u = _raw.get("usage", None)
                if hasattr(u, "__dict__"):
                    u = u.__dict__
                if isinstance(u, dict):
                    usage = {
                        "prompt_tokens": int(u.get("prompt_tokens", 0)),
                        "completion_tokens": int(u.get("completion_tokens", 0)),
                        "total_tokens": int(u.get("total_tokens", 0)),
                    }
                    # Estimation du coût
                    from core.agents.executor_llm import _estimate_cost
                    cost = _estimate_cost(
                        usage,
                        getattr(resp, "provider", None),
                        getattr(resp, "model_used", None)
                    )
            except Exception:
                usage = None

        # Log debug tokens + coût
        log.debug(
            "supervisor tokens=%s cost=%s",
            usage,
            cost
        )

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
            "usage": usage,
            "cost_estimate": cost,
            "prompts": {
                "system": truncate(_SUPERVISOR_SYSTEM, 2000),
                "user": truncate(_build_user_prompt(task), 4000),
            },
            "raw_hint": truncate(json.dumps(getattr(resp, "raw", None), ensure_ascii=False), MAX_RAW)
                if getattr(resp, "raw", None) is not None else None,
        }
        await storage.save_artifact(
            node_id="supervisor",
            content=json.dumps(trace, ensure_ascii=False, indent=2),
            ext=".llm.json"
        )

        # --- JSON strict uniquement
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Supervisor JSON invalide: objet JSON attendu.")
        for key in ("decompose", "subtasks", "plan"):
            if key not in data:
                raise ValueError(f"Supervisor JSON incomplet: clé manquante '{key}'.")
        if not isinstance(data["subtasks"], list):
            data["subtasks"] = []
        if not isinstance(data["plan"], list):
            data["plan"] = []
        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Supervisor JSON invalide: {e}; sortie={raw[:200]}")
    except (ProviderTimeout, ProviderUnavailable) as e:
        raise RuntimeError(f"Supervisor indisponible: {e}")