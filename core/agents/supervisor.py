"""
Superviseur — Version 'gratuit' via Ollama (LLM local).
Objectif :
- Générer un plan JSON STRICT pour le DAG : {decompose, plan[], risks, assumptions, notes}
- Valider avec Pydantic.
- Si invalide : re-prompt automatique (2 tentatives).
- En dernier recours : fallback déterministe (plan simple).

Tout est commenté en français pour la compréhension.
"""

import json
from typing import Optional
import os
from pydantic import BaseModel, ValidationError

from core.llm.providers.ollama import ollama_chat  # <-- provider local
# Si tu veux garder un mode "sans LLM", on testera USE_OLLAMA plus bas.


# -------- Schémas Pydantic : garantissent la structure du plan --------
class PlanNode(BaseModel):
    id: str
    title: str
    description: str = ""
    type: str = "task"  # "analysis", "research", "build", "write", "review", ...
    deps: list[str] = []
    acceptance: str = ""
    suggested_agent_role: str = "generic_executor"

class PlanOut(BaseModel):
    decompose: bool = True
    plan: list[PlanNode]
    risks: list[str] = []
    assumptions: list[str] = []
    notes: list[str] = []


# -------- Prompts (règles strictes pour forcer le JSON) --------
SYSTEM_PROMPT = (
    "Tu es un Superviseur IA expérimenté. "
    "Ta seule sortie doit être un JSON STRICT au format exact suivant, sans aucun texte autour:\n"
    "{\n"
    '  "decompose": bool,\n'
    '  "plan": [\n'
    '    {"id":"n1","title":"...","description":"...","type":"analysis|research|build|write|review",'
    '"deps":[],"acceptance":"...","suggested_agent_role":"generic_executor|writer|researcher|developer"}\n'
    "  ],\n"
    '  "risks": [], "assumptions": [], "notes": []\n'
    "}\n"
    "Si tu n'es pas sûr, produis le JSON le plus simple possible, mais toujours valide.\n"
)

# On construit le prompt utilisateur à partir de la tâche
def build_user_prompt(task_input: dict) -> str:
    title = task_input.get("title", "Tâche")
    desc = task_input.get("description", "")
    # On rappelle le sujet, et on insiste sur le JSON strict
    return (
        f"Tâche: {json.dumps(task_input, ensure_ascii=False)}\n\n"
        "Exigences:\n"
        "- Décomposer en sous-tâches si pertinent (parallélisables quand possible).\n"
        "- Chaque nœud doit avoir un id unique, un titre, une description, un type, des deps, et un critère d'acceptation.\n"
        "- Respecte le format exact demandé et ne renvoie *QUE* le JSON."
    )

# -------- Génération + validation + re-prompt en cas d'échec --------
async def _try_build_plan_once(task_input: dict) -> Optional[dict]:
    """
    Une tentative : on appelle le LLM local (Ollama) pour obtenir un JSON.
    Si le JSON est mal formé, on renvoie None.
    """
    user_prompt = build_user_prompt(task_input)
    raw = await ollama_chat(SYSTEM_PROMPT, user_prompt, temperature=0.2)
    # Le modèle peut parfois rajouter du texte parasite.
    # Stratégie simple : tenter un parse 'au plus large' en cherchant la première '{' et la dernière '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = raw[start:end+1]
    try:
        candidate = json.loads(snippet)
        # Validation Pydantic : renvoie une dict propre si ok
        return PlanOut.model_validate(candidate).model_dump()
    except Exception:
        return None

async def supervisor_plan(task_input: dict) -> dict:
    """
    Stratégie :
    1) Si USE_OLLAMA=1 → on tente 2 fois l'appel LLM + validation.
    2) Si toujours invalide (ou USE_OLLAMA≠1) → fallback déterministe.
    """
    use_ollama = os.getenv("USE_OLLAMA", "0") == "1"

    if use_ollama:
        for attempt in range(2):
            plan = await _try_build_plan_once(task_input)
            if plan:
                return plan
        # si les 2 tentatives échouent, on bascule vers le fallback

    # ===== Fallback déterministe (toujours valide) =====
    title = task_input.get("title", "Tâche")
    desc = task_input.get("description", "")
    fallback = {
        "decompose": True,
        "plan": [
            {
                "id": "n1",
                "title": f"Analyse A — {title}",
                "description": desc,
                "type": "analysis",
                "deps": [],
                "acceptance": "Texte A prêt",
                "suggested_agent_role": "generic_executor"
            },
            {
                "id": "n2",
                "title": f"Analyse B — {title}",
                "description": desc,
                "type": "analysis",
                "deps": [],
                "acceptance": "Texte B prêt",
                "suggested_agent_role": "generic_executor"
            },
            {
                "id": "n3",
                "title": "Synthèse finale",
                "description": "Fusion des parties A et B",
                "type": "write",
                "deps": ["n1","n2"],
                "acceptance": "Synthèse prête",
                "suggested_agent_role": "generic_executor"
            },
        ],
        "risks": [],
        "assumptions": [],
        "notes": ["fallback_plan"]
    }
    return PlanOut.model_validate(fallback).model_dump()
