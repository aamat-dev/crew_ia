from .registry import AgentSpec
from core.config import get_role_config


def recruit(role: str) -> AgentSpec:
    r = role.strip()
    exe_cfg = get_role_config("EXECUTOR")
    if r.lower().startswith("writer"):
        return AgentSpec(
            role,
            "core/agents/prompts/executors/writer_fr.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        )
    if r.lower().startswith("research"):
        return AgentSpec(
            role,
            "core/agents/prompts/executors/researcher.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        )
    if r.lower().startswith("review"):
        return AgentSpec(
            role,
            "core/agents/prompts/executors/reviewer.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        )
    # fallback manager
    man_cfg = get_role_config("MANAGER")
    return AgentSpec(
        role,
        "core/agents/prompts/manager.txt",
        man_cfg.provider,
        man_cfg.model,
        [],
    )
