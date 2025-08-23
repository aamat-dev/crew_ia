from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pydantic import ValidationError

from .registry import resolve_agent, AgentSpec
from .recruiter import recruit
from .schemas import SupervisorPlan, parse_supervisor_json
from core.llm.providers.base import LLMRequest
from core.llm import runner as llm_runner


async def run(task: Dict[str, Any], storage: Any = None) -> SupervisorPlan:
    """Exécute le rôle Supervisor et renvoie un plan validé."""

    try:
        spec: AgentSpec = resolve_agent("Supervisor")
    except KeyError:
        spec = recruit("Supervisor")

    if getattr(spec, "system_prompt", None):
        system_prompt = spec.system_prompt
    elif getattr(spec, "system_prompt_path", None):
        sp = Path(spec.system_prompt_path)
        if not sp.is_absolute():
            repo_root = Path(__file__).resolve().parents[2]
            sp = repo_root / sp
        system_prompt = sp.read_text(encoding="utf-8")
    else:
        raise ValueError("Prompt système du Supervisor introuvable")

    task_json = json.dumps(task, ensure_ascii=False)
    user_msg = task_json
    last_err: ValidationError | None = None

    for _ in range(3):
        req = LLMRequest(
            system=system_prompt,
            prompt=user_msg,
            model=spec.model,
            provider=spec.provider,
        )
        resp = await llm_runner.run_llm(req)
        try:
            return parse_supervisor_json(resp.text)
        except ValidationError as ve:
            last_err = ve
            user_msg = (
                task_json
                + "\nLa réponse précédente n'était pas un JSON valide. "
                + "Réponds uniquement avec un JSON valide conforme au schéma."
            )

    if last_err:
        raise last_err
    raise RuntimeError("Unexpected supervisor failure")
