from __future__ import annotations
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.llm import call_json  # doit retourner un dict JSON
from api.fastapi_app.clients.feedbacks import create_feedback  # POST /feedbacks

CHECKLISTS_ROOT = Path("quality/checklists")
CHECKLISTS_ALIAS = CHECKLISTS_ROOT / "latest"

def _resolve_checklist_path(node_type: str, version: Optional[str] = None) -> Path:
    if version is None:
        if CHECKLISTS_ALIAS.is_symlink():
            version_dir = CHECKLISTS_ALIAS.resolve().name
        else:
            version_dir = CHECKLISTS_ALIAS.read_text().strip()
    else:
        version_dir = version
    return CHECKLISTS_ROOT / version_dir / f"qa.{node_type}.v1.json"

def load_checklist(node_type: str, version: Optional[str] = None) -> Dict[str, Any]:
    p = _resolve_checklist_path(node_type, version)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def build_prompts(checklist: Dict[str, Any], node: Any, run: Any, artifact_text: str) -> tuple[str, str]:
    """Construit (system, user) à partir des fichiers versionnés."""
    prompts_dir = Path("quality/prompts") / checklist["version"]
    with open(prompts_dir / "reviewer.system.txt", "r", encoding="utf-8") as f:
        sys = f.read()
    with open(prompts_dir / "reviewer.user.md", "r", encoding="utf-8") as f:
        user_tmpl = f.read()
    node_type = getattr(node, "role", None) or getattr(node, "type", None)
    node_meta = {
        "id": str(node.id),
        "type": node_type,
        "run_id": str(run.id),
    }
    user = (
        user_tmpl
        .replace("{{CHECKLIST_JSON}}", json.dumps(checklist, ensure_ascii=False, indent=2))
        .replace("{{NODE_META}}", json.dumps(node_meta, ensure_ascii=False, indent=2))
        .replace("{{LIVRABLE}}", artifact_text)
    )
    return sys, user

async def write_sidecar(node: Any, data: Dict[str, Any]) -> None:
    """Écrit {ts}.qa.json à côté du llm.json si disponible ; sinon dans le répertoire node."""
    base = getattr(node, "sidecars_dir", None)
    if base is None:
        base = Path("runs") / str(node.run_id) / "nodes" / str(node.id)
    base.mkdir(parents=True, exist_ok=True)
    ts = getattr(node, "ended_at_iso", None) or "now"
    out = base / f"{ts}.qa.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def post_node_hook(node: Any, run: Any, artifact_text: str, *, timeout_s: int = 30) -> None:
    """
    Hook post-nœud : appelle le reviewer LLM avec la checklist du node.type,
    persiste un feedback auto (Fil J) et écrit un sidecar .qa.json.
    Non bloquant : en cas d'échec/timeout, log + sortie gracieuse.
    """
    node_type = getattr(node, "role", None) or getattr(node, "type", None)
    checklist = load_checklist(node_type, version=None)
    sys_prompt, user_prompt = build_prompts(checklist, node, run, artifact_text)
    content_hash = sha256_text(artifact_text or "")
    try:
        eval_json = await asyncio.wait_for(
            call_json(
                system=sys_prompt,
                user=user_prompt,
                model=getattr(run, "review_model", "openai:gpt-4o-mini"),
                json_mode=True,
                temperature=0.0,
            ),
            timeout=timeout_s,
        )
        eval_json.setdefault("meta", {})["content_sha256"] = content_hash
        score = int(eval_json.get("overall_score", 0))
        comment = (eval_json.get("summary_comment") or "")[:400]
        feedback_payload = {
            "run_id": str(run.id),
            "node_id": str(node.id),
            "source": "auto",
            "reviewer": "agent:qa-reviewer@v1",
            "score": score,
            "comment": comment,
            "evaluation": eval_json,
        }
        headers = {}
        req_id = getattr(node, "request_id", None)
        if req_id:
            headers["X-Request-ID"] = req_id
        await create_feedback(feedback_payload, headers=headers)
        await write_sidecar(node, eval_json)
    except asyncio.TimeoutError:
        print(f"[qa_reviewer] timeout after {timeout_s}s on node {node.id}")
    except Exception as e:  # pragma: no cover - log
        print(f"[qa_reviewer] error on node {node.id}: {e}")
