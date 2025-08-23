from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from core.config import get_role_config


@dataclass
class AgentSpec:
    role: str
    system_prompt: str
    provider: str
    model: str
    tools: List[str]


# matrice statique: role -> (chemin prompt, role config, outils)
_AGENT_MATRIX: Dict[str, tuple[str, str, List[str]]] = {
    "Supervisor": (
        "core/agents/prompts/supervisor.txt",
        "SUPERVISOR",
        [],
    ),
    "Manager_Generic": (
        "core/agents/prompts/manager.txt",
        "MANAGER",
        [],
    ),
    "Writer_FR": (
        "core/agents/prompts/executors/writer_fr.txt",
        "EXECUTOR",
        [],
    ),
    "Researcher": (
        "core/agents/prompts/executors/researcher.txt",
        "EXECUTOR",
        [],
    ),
    "Reviewer": (
        "core/agents/prompts/executors/reviewer.txt",
        "EXECUTOR",
        [],
    ),
}

_ROOT = Path(__file__).resolve().parents[2]
_DYNAMIC_REGISTRY: Dict[str, AgentSpec] = {}


def register_agent(spec: AgentSpec) -> None:
    _DYNAMIC_REGISTRY[spec.role] = spec


def resolve_agent(role: str) -> AgentSpec:
    """Retourne la configuration d'un agent selon son rôle."""
    if role in _DYNAMIC_REGISTRY:
        return _DYNAMIC_REGISTRY[role]
    spec = _AGENT_MATRIX.get(role)
    if not spec:
        raise KeyError(role)
    prompt_path, cfg_role, tools = spec
    cfg = get_role_config(cfg_role)
    system_prompt = (_ROOT / prompt_path).read_text(encoding="utf-8")
    return AgentSpec(
        role=role,
        system_prompt=system_prompt,
        provider=cfg.provider,
        model=cfg.model,
        tools=list(tools),
    )


def load_default_registry() -> Dict[str, AgentSpec]:

    """Compat: construit un registre pour les rôles connus."""
    return {r: resolve_agent(r) for r in _AGENT_MATRIX}

