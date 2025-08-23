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


# Registry global, initialisé vide (rôles par défaut résolus à la volée)
_REGISTRY: Dict[str, AgentSpec] = {}


def register_agent(spec: AgentSpec) -> None:
    """Ajoute ou remplace la spécification d'un agent dans le registry."""
    _REGISTRY[spec.role] = spec


def resolve_agent(role: str) -> AgentSpec:
    """Retourne la spec d'un agent.
    - Si enregistrée dynamiquement → retourne la version dynamique.
    - Sinon → reconstruit depuis la config courante.
    """
    if role in _REGISTRY:
        return _REGISTRY[role]
    registry = load_default_registry()
    if role in registry:
        return registry[role]
    raise KeyError(role)


def clear_registry() -> None:
    """Vide le registre dynamique (utile pour les tests)."""
    _REGISTRY.clear()
