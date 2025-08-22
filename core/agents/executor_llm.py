PROMPT_TRUNC = 800
from pathlib import Path
import json

from .registry import load_default_registry
from .recruiter import recruit
from .schemas import PlanNodeModel
from core.llm.providers.base import LLMRequest
from core.llm.runner import run_llm
from core.storage.composite_adapter import CompositeAdapter


async def agent_runner(node: PlanNodeModel, storage: CompositeAdapter | None = None) -> dict:
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
    final_prompt = f"{system_prompt}\n{user_msg}" if system_prompt else user_msg
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

    meta = {
        "provider": getattr(resp, "provider", None),
        "model": getattr(resp, "model_used", getattr(resp, "model", None)),
        "latency_ms": getattr(resp, "latency_ms", getattr(resp, "duration_ms", None)),
        "usage": getattr(resp, "usage", None),
        "prompts": {
            "system": (system_prompt or "")[:PROMPT_TRUNC],
            "user": (user_msg or "")[:PROMPT_TRUNC],
            "final": (final_prompt or "")[:PROMPT_TRUNC],
        },
    }
    return {"markdown": content, "llm": meta}


async def agent_runner_legacy(node: PlanNodeModel, storage: CompositeAdapter) -> str:
    """Shim de compatibilité: écrit les artifacts et renvoie le chemin Markdown."""
    res = await agent_runner(node, None)
    md = res.get("markdown", "")
    meta = res.get("llm", {})

    node_dbid = getattr(node, "db_id", None)
    if node_dbid:
        await storage.save_artifact(node_id=str(node_dbid), content=md, ext=".md")
        if meta:
            await storage.save_artifact(
                node_id=str(node_dbid),
                content=json.dumps(meta, ensure_ascii=False, indent=2),
                ext=".llm.json",
            )

    path = f"artifact_{node.id}.md"
    Path(path).write_text(md, encoding="utf-8")
    if meta:
        Path(path.replace(".md", ".llm.json")).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return path
