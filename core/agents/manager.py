import json
from typing import List

from pydantic import ValidationError

from .schemas import PlanNodeModel, ManagerOutput, parse_manager_json
from .registry import resolve_agent, AgentSpec
from .recruiter import recruit
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm

async def run_manager(subplan: List[PlanNodeModel]) -> ManagerOutput:
    try:
        spec: AgentSpec = resolve_agent("Manager_Generic")
    except KeyError:
        spec = recruit("Manager_Generic")
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
    task_json = json.dumps(payload, ensure_ascii=False)
    user_msg = task_json
    last_err: Exception | None = None
    for _ in range(3):
        req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
        resp = await run_llm(req)
        try:
            out = parse_manager_json(resp.text)
            ids = {n.id for n in subplan}
            for a in out.assignments:
                if a.node_id not in ids:
                    raise ValueError(f"Unknown node_id {a.node_id} in assignment")
            return out
        except (ValidationError, ValueError) as err:
            last_err = err
            user_msg = task_json + "\nLa réponse précédente n'était pas un JSON valide. Réponds uniquement avec un JSON valide conforme au schéma."
    raise last_err if last_err else RuntimeError("Unexpected manager failure")
