# core/io/artifacts_fs.py
from __future__ import annotations

import os, json
from pathlib import Path
from typing import Optional, Dict, Any
from orchestrator.sidecars import normalize_llm_sidecar

def runs_root() -> Path:
    return Path(os.getenv("ARTIFACTS_DIR") or os.getenv("RUNS_ROOT") or ".runs")

def node_dir(run_id: str, node_key: str) -> Path:
    return runs_root() / run_id / "nodes" / node_key

def md_path(run_id: str, node_key: str) -> Path:
    return node_dir(run_id, node_key) / f"artifact_{node_key}.md"

def llm_sidecar_path(run_id: str, node_key: str) -> Path:
    return node_dir(run_id, node_key) / f"artifact_{node_key}.llm.json"

def ensure_dirs(run_id: str, node_key: str) -> Path:
    nd = node_dir(run_id, node_key)
    nd.mkdir(parents=True, exist_ok=True)
    return nd

def write_md(run_id: str, node_key: str, content_md: str) -> Path:
    ensure_dirs(run_id, node_key)
    p = md_path(run_id, node_key)
    p.write_text(content_md, encoding="utf-8")
    return p

def write_llm_sidecar(
    run_id: str, node_key: str, meta: Dict[str, Any], node_id: str | None = None
) -> Dict[str, Any]:
    """Écrit un sidecar LLM normalisé et le retourne."""
    ensure_dirs(run_id, node_key)
    p = llm_sidecar_path(run_id, node_key)
    meta_norm = normalize_llm_sidecar(meta, run_id=run_id, node_id=node_id)
    p.write_text(json.dumps(meta_norm, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta_norm

def read_first_llm_meta(run_id: str, node_key: str) -> Dict[str, Any]:
    """
    Lecture robuste: .runs/<run>/nodes/<key>/*.llm.json
    Retourne {} si rien.
    """
    nd = node_dir(run_id, node_key)
    if not nd.is_dir():
        return {}
    preferred = [llm_sidecar_path(run_id, node_key)]
    candidates = preferred + sorted(nd.glob("*.llm.json"))
    for p in candidates:
        try:
            if p.exists():
                obj = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    return {
                        "provider": obj.get("provider"),
                        "model": obj.get("model_used") or obj.get("model"),
                        "latency_ms": obj.get("latency_ms"),
                        "usage": obj.get("usage"),
                    }
        except Exception:
            continue
    return {}

# ---- Compat lecture layout ancien: fichiers plats à la racine .runs/ ----

def legacy_llm_sidecar_path(node_key: str) -> Path:
    return runs_root() / f"artifact_{node_key}.llm.json"

def read_legacy_llm_meta(node_key: str) -> Dict[str, Any]:
    p = legacy_llm_sidecar_path(node_key)
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                return {
                    "provider": obj.get("provider"),
                    "model": obj.get("model_used") or obj.get("model"),
                    "latency_ms": obj.get("latency_ms"),
                    "usage": obj.get("usage"),
                }
        except Exception:
            pass
    return {}
