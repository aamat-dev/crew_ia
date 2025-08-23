import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from .schemas import PlanNodeModel, ManagerOutput, parse_manager_json
from .registry import AgentSpec, resolve_agent
from .recruiter import recruit
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm


async def run_manager(subplan: List[PlanNodeModel]) -> ManagerOutput:
    """Attribue les nœuds d'un sous-plan aux agents exécutants.

    En cas de réponse JSON invalide, le LLM est relancé jusqu'à deux fois.
    """

    try:
        spec: AgentSpec = resolve_agent("Manager_Generic")
    except KeyError:
        spec = recruit("Manager_Generic")

    # Prépare le contexte et le message utilisateur
    system_prompt: str
    if getattr(spec, "system_prompt", None):
        system_prompt = spec.system_prompt
    else:
        sp = Path(spec.system_prompt_path)
        if not sp.is_absolute():
            repo_root = Path(__file__).resolve().parents[2]
            sp = repo_root / sp
        system_prompt = sp.read_text(encoding="utf-8")
    payload = [
        {
            "id": n.id,
            "title": n.title,
            "type": n.type,
            "role": n.suggested_agent_role,
            "acceptance": n.acceptance,
            "deps": n.deps,
        }
        for n in subplan
    ]
    base_prompt = json.dumps(payload, ensure_ascii=False)

    attempts = 0
    last_err: Exception | None = None
    ids = {n.id for n in subplan}

    # Boucle de re-prompt en cas d'échec de validation
    while attempts < 3:
        prompt = base_prompt
        if attempts and last_err is not None:
            prompt += (
                f"\n\nLa réponse précédente était invalide ({last_err}). "
                "Merci de fournir uniquement un JSON conforme au schéma "
                "ManagerOutput."
            )

        req = LLMRequest(
            system=system_prompt,
            prompt=prompt,
            model=spec.model,
            provider=spec.provider,
        )
        resp = await run_llm(req)

        try:
            out = parse_manager_json(resp.text)

            # Vérifier l'existence des node_id dans le sous-plan
            for a in out.assignments:
                if a.node_id not in ids:
                    raise ValueError(f"Unknown node_id {a.node_id} in assignment")

            return out
        except (ValidationError, ValueError) as err:  # Re-tenter avec info d'erreur
            attempts += 1
            last_err = err

    # Après trois essais, propager la dernière erreur
    raise last_err if last_err is not None else RuntimeError("Unknown error")
