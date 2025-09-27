from __future__ import annotations

import json
from typing import Any, Dict

from pydantic import ValidationError

from .registry import resolve_agent
from .recruiter import arecruit
from .schemas import SupervisorPlan, parse_supervisor_json
from core.llm.providers.base import LLMRequest
from core.llm import runner as llm_runner


async def run(task: Dict[str, Any], storage: Any = None) -> SupervisorPlan:
    """
    Execute the Supervisor role once and return a validated SupervisorPlan.
    """

    try:
        spec = resolve_agent("Supervisor")
    except KeyError:
        spec = await arecruit("Supervisor")

    system_prompt = spec.system_prompt

    task_json = json.dumps(task, ensure_ascii=False)
    user_msg = task_json
    last_err: Exception | None = None
    for _ in range(3):
        req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
        resp = await llm_runner.run_llm(req)
        # Tolérance: supprime les éventuelles fences Markdown (```json ... ```)
        txt = resp.text.strip() if isinstance(resp.text, str) else str(resp.text)
        if txt.startswith("```"):
            # enlève les 1ères et dernières fences
            txt = txt.strip().lstrip("`").lstrip("json").lstrip().rstrip("`").strip()
        try:
            plan = parse_supervisor_json(txt)
            return plan
        except ValidationError as err:
            last_err = err
            user_msg = (
                task_json
                + "\nLa réponse précédente n'était pas un JSON valide. Réponds uniquement avec un JSON valide conforme au schéma."
            )

    raise last_err or RuntimeError("Supervisor output invalid")
