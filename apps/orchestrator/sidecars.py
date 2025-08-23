from __future__ import annotations

"""Utilitaires de normalisation des sidecars LLM."""

from typing import Any, Dict, List
import uuid
import datetime as dt

PROMPT_TRUNC = 800


def _truncate_prompt(val: Any) -> Any:
    """Tronque récursivement les contenus de prompt à 800 caractères."""
    if isinstance(val, str):
        return val[:PROMPT_TRUNC]
    if isinstance(val, list):
        out: List[Any] = []
        for item in val:
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    item = {**item, "content": content[:PROMPT_TRUNC]}
            elif isinstance(item, str):
                item = item[:PROMPT_TRUNC]
            out.append(item)
        return out
    if isinstance(val, dict):
        return {k: _truncate_prompt(v) for k, v in val.items()}
    return val


def _to_uuid(v: Any) -> str | None:
    try:
        u = uuid.UUID(str(v))
        if u.version == 4:
            return str(u)
    except Exception:
        return None
    return None


def _rfc3339(ts: Any) -> str:
    if isinstance(ts, dt.datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        return ts.isoformat()
    if isinstance(ts, str):
        try:
            parsed = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.isoformat()
        except Exception:
            pass
    now = dt.datetime.now(dt.timezone.utc)
    return now.isoformat()


def normalize_llm_sidecar(data: Dict[str, Any] | None, *, run_id: str | None = None, node_id: str | None = None) -> Dict[str, Any]:
    """Normalise un sidecar LLM en respectant la spec v1.0."""
    out: Dict[str, Any] = dict(data or {})

    # version
    out["version"] = "1.0"

    # provider (défaut 'other')
    provider = out.get("provider") or "other"
    if provider not in {"openai", "anthropic", "ollama", "azure_openai", "other"}:
        provider = "other"
    out["provider"] = provider

    # run_id / node_id
    rid = _to_uuid(run_id or out.get("run_id"))
    if rid:
        out["run_id"] = rid
    nid = _to_uuid(node_id or out.get("node_id"))
    if nid:
        out["node_id"] = nid

    # model / model_used harmonisation
    warnings: List[str] = list(out.get("warnings") or [])
    model = out.get("model")
    model_used = out.get("model_used")
    if model and model_used and model != model_used:
        warnings.append("model/model_used mismatch (normalized)")
    final_model = model_used or model
    if final_model:
        out["model"] = final_model
        out["model_used"] = final_model

    if warnings:
        out["warnings"] = warnings

    # latency
    try:
        lat = int(out.get("latency_ms") or 0)
    except Exception:
        lat = 0
    if lat < 0:
        lat = 0
    out["latency_ms"] = lat

    # usage tokens
    usage = dict(out.get("usage") or {})
    for k in ("prompt_tokens", "completion_tokens"):
        try:
            v = int(usage.get(k) or 0)
        except Exception:
            v = 0
        if v < 0:
            v = 0
        usage[k] = v
    out["usage"] = usage

    # cost
    cost = dict(out.get("cost") or {})
    try:
        est = float(cost.get("estimated") or 0)
    except Exception:
        est = 0.0
    if est < 0:
        est = 0.0
    cost["estimated"] = est
    out["cost"] = cost

    # prompts
    prompts = dict(out.get("prompts") or {})
    prompts["system"] = _truncate_prompt(prompts.get("system", ""))
    prompts["user"] = _truncate_prompt(prompts.get("user", ""))
    if "final" in prompts:
        prompts["final"] = _truncate_prompt(prompts["final"])
    out["prompts"] = prompts

    # timestamps
    ts = dict(out.get("timestamps") or {})
    ts_start = ts.get("started_at")
    ts_end = ts.get("ended_at")
    if not ts_start:
        ts_start = dt.datetime.now(dt.timezone.utc)
    if not ts_end:
        ts_end = ts_start
    ts["started_at"] = _rfc3339(ts_start)
    ts["ended_at"] = _rfc3339(ts_end)
    out["timestamps"] = ts

    return out
