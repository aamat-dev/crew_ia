import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class AgentSpec:
    role: str
    system_prompt_path: str
    provider: str
    model: str
    tools: list[str]


def _resolve_provider_model(prefix: str) -> tuple[str, str]:
    """Résout provider/modèle à partir des variables d'environnement.

    PREFIX_PROVIDER et PREFIX_MODEL sont utilisés en priorité, sinon on
    retombe sur LLM_DEFAULT_PROVIDER / LLM_DEFAULT_MODEL."""

    provider = os.getenv(f"{prefix}_PROVIDER", os.getenv("LLM_DEFAULT_PROVIDER", "ollama"))
    model = os.getenv(f"{prefix}_MODEL", os.getenv("LLM_DEFAULT_MODEL", "llama3.1:8b"))
    return provider, model


# Rôles connus -> (fichier prompt, préfixe env)
ROLE_PROMPTS: Dict[str, tuple[str, str]] = {
    "Supervisor": ("core/agents/prompts/supervisor.txt", "SUPERVISOR"),
    "Manager_Generic": ("core/agents/prompts/manager.txt", "MANAGER"),
    "Writer_FR": ("core/agents/prompts/executors/writer_fr.txt", "EXECUTOR"),
    "Researcher": ("core/agents/prompts/executors/researcher.txt", "EXECUTOR"),
    "Reviewer": ("core/agents/prompts/executors/reviewer.txt", "EXECUTOR"),
}


def load_default_registry() -> Dict[str, AgentSpec]:
    """Charge les specs par défaut pour les rôles connus.

    Pour ajouter un nouveau rôle, compléter ROLE_PROMPTS avec
    ("NomDuRôle", ("chemin/prompt.txt", "PREFIX_ENV")). Le provider et le
    modèle seront automatiquement résolus via PREFIX_ENV_PROVIDER/MODEL avec
    fallback sur LLM_DEFAULT_PROVIDER/MODEL."""

    registry: Dict[str, AgentSpec] = {}
    for role, (prompt, prefix) in ROLE_PROMPTS.items():
        provider, model = _resolve_provider_model(prefix)
        registry[role] = AgentSpec(role, prompt, provider, model, [])
    return registry
