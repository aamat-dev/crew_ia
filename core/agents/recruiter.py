from pathlib import Path

from .registry import AgentSpec, register_agent
from core.config import get_role_config


def recruit(role: str) -> AgentSpec:
    r = role.strip()
    root = Path(__file__).resolve().parents[2]
    exe_cfg = get_role_config("EXECUTOR")
    if r.lower().startswith("writer"):
        prompt = (root / "core/agents/prompts/executors/writer_fr.txt").read_text(encoding="utf-8")
        spec = AgentSpec(role, prompt, exe_cfg.provider, exe_cfg.model, [])
        register_agent(spec)
        return spec
    if r.lower().startswith("research"):
        prompt = (root / "core/agents/prompts/executors/researcher.txt").read_text(encoding="utf-8")
        spec = AgentSpec(role, prompt, exe_cfg.provider, exe_cfg.model, [])
        register_agent(spec)
        return spec
    if r.lower().startswith("review"):
        prompt = (root / "core/agents/prompts/executors/reviewer.txt").read_text(encoding="utf-8")
        spec = AgentSpec(role, prompt, exe_cfg.provider, exe_cfg.model, [])
        register_agent(spec)
        return spec
    # fallback manager
    man_cfg = get_role_config("MANAGER")
    prompt = (root / "core/agents/prompts/manager.txt").read_text(encoding="utf-8")
    spec = AgentSpec(role, prompt, man_cfg.provider, man_cfg.model, [])
    register_agent(spec)
    return spec
