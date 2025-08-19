from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict

from pydantic import ValidationError

from .registry import load_default_registry
from .recruiter import recruit
from .schemas import SupervisorPlan, parse_supervisor_json
from core.llm.providers.base import LLMRequest
from core.llm import runner as llm_runner

async def run(task: Dict[str, Any], storage: Any = None) -> SupervisorPlan:
    """
    Execute the Supervisor role once and return a validated SupervisorPlan.
    """
    registry = load_default_registry()
    spec = registry.get("Supervisor") or recruit("Supervisor")

    root = Path(__file__).resolve().parents[2]
    system_prompt = (root / spec.system_prompt_path).read_text(encoding="utf-8")

    user_msg = json.dumps(task, ensure_ascii=False)
    req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
    resp = await llm_runner.run_llm(req)

    try:
        plan = parse_supervisor_json(resp.text)
    except ValidationError as ve:
        raise ve
    return plan
