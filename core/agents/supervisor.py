from pathlib import Path
import json
from typing import Any, Dict

from pydantic import ValidationError

from .registry import load_default_registry
from .recruiter import recruit
from .schemas import SupervisorPlan, parse_supervisor_json
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm


async def run(task: Dict[str, Any], storage: Any | None = None) -> SupervisorPlan:
    """Génère un plan via le rôle Supervisor.

    Parameters
    ----------
    task: dict
        Description structurée de la tâche (titre, description, acceptance).
    storage: Any, optional
        Paramètre conservé pour compatibilité future (non utilisé).

    Returns
    -------
    SupervisorPlan
        Plan validé (pas de cycles, dépendances existantes, rôle non vide).
    """

    task_input = json.dumps(task, ensure_ascii=False)
    spec = load_default_registry().get("Supervisor") or recruit("Supervisor")
    root = Path(__file__).resolve().parents[2]
    system_prompt = (root / spec.system_prompt_path).read_text(encoding="utf-8")
    req = LLMRequest(system=system_prompt, prompt=task_input, model=spec.model, provider=spec.provider)
    for attempt in range(2):
        resp = await run_llm(req)
        try:
            return parse_supervisor_json(resp.text)
        except ValidationError:
            if attempt == 0:
                req.prompt = task_input + "\nRAPPEL: répondez UNIQUEMENT en JSON strict valide."
            else:
                raise
