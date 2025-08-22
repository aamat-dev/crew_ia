from dataclasses import dataclass
from typing import Dict

from core.config import get_role_config


@dataclass
class AgentSpec:
    role: str
    system_prompt_path: str
    provider: str
    model: str
    tools: list[str]


def load_default_registry() -> Dict[str, AgentSpec]:
    sup_cfg = get_role_config("SUPERVISOR")
    man_cfg = get_role_config("MANAGER")
    exe_cfg = get_role_config("EXECUTOR")
    return {
        "Supervisor": AgentSpec(
            "Supervisor",
            "core/agents/prompts/supervisor.txt",
            sup_cfg.provider,
            sup_cfg.model,
            [],
        ),
        "Manager_Generic": AgentSpec(
            "Manager_Generic",
            "core/agents/prompts/manager.txt",
            man_cfg.provider,
            man_cfg.model,
            [],
        ),
        "Writer_FR": AgentSpec(
            "Writer_FR",
            "core/agents/prompts/executors/writer_fr.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        ),
        "Researcher": AgentSpec(
            "Researcher",
            "core/agents/prompts/executors/researcher.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        ),
        "Reviewer": AgentSpec(
            "Reviewer",
            "core/agents/prompts/executors/reviewer.txt",
            exe_cfg.provider,
            exe_cfg.model,
            [],
        ),
    }
