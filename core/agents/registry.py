from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from core.config import get_role_config


@dataclass
class AgentSpec:
    role: str
    system_prompt: str
    provider: str
    model: str
    tools: list[str]


_AGENT_MATRIX: Dict[str, tuple[str, str]] = {
    "Supervisor": ("core/agents/prompts/supervisor.txt", "SUPERVISOR"),
    "Manager_Generic": ("core/agents/prompts/manager.txt", "MANAGER"),
    "Writer_FR": (
        "core/agents/prompts/executors/writer_fr.txt",
        "EXECUTOR",
    ),
    "Researcher": (
        "core/agents/prompts/executors/researcher.txt",
        "EXECUTOR",
    ),
    "Reviewer": (
        "core/agents/prompts/executors/reviewer.txt",
        "EXECUTOR",
    ),
}


_DYNAMIC_REGISTRY: Dict[str, AgentSpec] = {}


def _read_prompt(rel: str) -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / rel).read_text(encoding="utf-8")


def resolve_agent(role: str) -> AgentSpec:
    if role in _DYNAMIC_REGISTRY:
        return _DYNAMIC_REGISTRY[role]
    if role in _AGENT_MATRIX:
        prompt_path, cfg_key = _AGENT_MATRIX[role]
        cfg = get_role_config(cfg_key)
        prompt = _read_prompt(prompt_path)
        return AgentSpec(role, prompt, cfg.provider, cfg.model, [])
    raise KeyError(role)


def register_agent(spec: AgentSpec) -> None:
    _DYNAMIC_REGISTRY[spec.role] = spec


def load_default_registry() -> Dict[str, AgentSpec]:
    return {role: resolve_agent(role) for role in _AGENT_MATRIX} | _DYNAMIC_REGISTRY

