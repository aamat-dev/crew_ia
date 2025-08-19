import json
from pathlib import Path
from typing import List
from pydantic import ValidationError

from .schemas import PlanNodeModel, ManagerOutput, parse_manager_json
from .registry import load_default_registry, AgentSpec
from .recruiter import recruit
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm

async def run_manager(subplan: List[PlanNodeModel]) -> ManagerOutput:
    registry = load_default_registry()
    spec: AgentSpec = registry.get("Manager_Generic") or recruit("Manager_Generic")
    root = Path(__file__).resolve().parents[2]
    system_prompt = (root / spec.system_prompt_path).read_text(encoding="utf-8")
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
    user_msg = json.dumps(payload, ensure_ascii=False)
    req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
    resp = await run_llm(req)
    out = parse_manager_json(resp.text)
    ids = {n.id for n in subplan}
    for a in out.assignments:
        if a.node_id not in ids:
            raise ValidationError(f"Unknown node_id {a.node_id} in assignment")
    if not out.quality_checks:
        out.quality_checks.append("Vérifier conformité aux critères d'acceptation.")
    return out
