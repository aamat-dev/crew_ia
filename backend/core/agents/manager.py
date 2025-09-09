import json
from typing import List

from pydantic import ValidationError

from .schemas import PlanNodeModel, ManagerOutput, parse_manager_json
from .registry import resolve_agent, AgentSpec
from .recruiter import arecruit
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm


async def run_manager(subplan: List[PlanNodeModel]) -> ManagerOutput:
    try:
        spec: AgentSpec = resolve_agent("Manager_Generic")
    except KeyError:
        spec = await arecruit("Manager_Generic")
    system_prompt = spec.system_prompt

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
    ids = {n.id for n in subplan}
    prompt = base_prompt
    last_err: Exception | None = None
    for _ in range(3):
        req = LLMRequest(system=system_prompt, prompt=prompt, model=spec.model, provider=spec.provider)
        resp = await run_llm(req)
        try:
            out = parse_manager_json(resp.text)
            for a in out.assignments:
                if a.node_id not in ids:
                    raise ValueError(f"Unknown node_id {a.node_id} in assignment")
            if not out.quality_checks:
                out.quality_checks.append("Vérifier conformité aux critères d'acceptation.")
            return out
        except (ValidationError, ValueError) as err:
            last_err = err
            prompt = (
                base_prompt
                + f"\n\nLa réponse précédente était invalide ({err}). Merci de fournir uniquement un JSON conforme au schéma ManagerOutput."
            )
    raise last_err or RuntimeError("Manager output invalid")
