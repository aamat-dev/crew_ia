from __future__ import annotations
import json
from typing import Any, Dict

from pydantic import ValidationError

from .registry import resolve_agent, AgentSpec
from .recruiter import recruit
from .schemas import SupervisorPlan, parse_supervisor_json
from core.llm.providers.base import LLMRequest
from core.llm import runner as llm_runner

async def run(task: Dict[str, Any], storage: Any = None) -> SupervisorPlan:
    """
    Execute the Supervisor role once and return a validated SupervisorPlan.
    """
    try:
        spec: AgentSpec = resolve_agent("Supervisor")
    except KeyError:
        spec = recruit("Supervisor")
    system_prompt = spec.system_prompt

    task_json = json.dumps(task, ensure_ascii=False)
    user_msg = task_json
    last_err: ValidationError | None = None
    for _ in range(3):
        req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
        resp = await llm_runner.run_llm(req)
        try:
            return parse_supervisor_json(resp.text)
        except ValidationError as ve:
            last_err = ve
            user_msg = task_json + "\nLa réponse précédente n'était pas un JSON valide. Réponds uniquement avec un JSON valide conforme au schéma."
    raise last_err if last_err else RuntimeError("Unexpected supervisor failure")
