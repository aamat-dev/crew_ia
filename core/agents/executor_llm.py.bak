import json
import logging
from pathlib import Path

from .registry import load_default_registry
from .recruiter import recruit
from .schemas import PlanNodeModel
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm

log = logging.getLogger("crew.executor")


async def agent_runner(node: PlanNodeModel, storage) -> str:
    role = node.suggested_agent_role
    spec = load_default_registry().get(role) or recruit(role)

    root = Path(__file__).resolve().parents[2]
    system_prompt = (root / spec.system_prompt_path).read_text(encoding="utf-8")

    brief = [f"Titre: {node.title}"]
    if node.acceptance:
        brief.append("Acceptance: " + "; ".join(node.acceptance))
    if node.notes:
        brief.append("Notes: " + "; ".join(node.notes))
    user_msg = "\n".join(brief)

    req = LLMRequest(system=system_prompt, prompt=user_msg, model=spec.model, provider=spec.provider)
    resp = await run_llm(req)

    content = resp.text.strip()
    if role == "Writer_FR":
        content = f"# {node.title}\n\n{content}\n"
    elif role == "Researcher":
        content = (
            "## Objectif\n\n" + content + "\n\n## Méthode\n\n- \n\n## Faits clés\n\n- \n\n## Limites\n\n- \n\n## Sources\n\n- "
        )
    elif role == "Reviewer":
        content = (
            "### Checklist cochée\n" + content + "\n\n### Corrections proposées\n\n- \n\n### Risques résiduels\n\n- "
        )

    await storage.save_artifact(node_id=node.id, content=content, ext=".md")
    sidecar = {
        "role": role,
        "provider": getattr(resp, "provider", None),
        "model": getattr(resp, "model_used", None),
        "latency_ms": getattr(resp, "latency_ms", None),
        "usage": getattr(resp, "usage", None),
        "prompts": {
            "system": (system_prompt or "")[:800],
            "user": (user_msg or "")[:800],
        },
    }
    await storage.save_artifact(
        node_id=node.id,
        content=json.dumps(sidecar, ensure_ascii=False, indent=2),
        ext=".llm.json",
    )
    log.info("executor role=%s provider=%s model=%s", role, resp.provider, resp.model_used)
    return f"artifact_{node.id}.md"
