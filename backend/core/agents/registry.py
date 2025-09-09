from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Modèles DB Agents
from backend.api.fastapi_app.models.agent import (
    AgentTemplate,
    AgentModelsMatrix,
)

log = logging.getLogger(__name__)


@dataclass
class AgentSpec:
    role: str
    system_prompt: str | None
    provider: str
    model: str
    tools: List[str]


# Registre dynamique en mémoire: rempli par le recruiter DB
_DYNAMIC_REGISTRY: Dict[str, AgentSpec] = {}


def register_agent(spec: AgentSpec) -> None:
    _DYNAMIC_REGISTRY[spec.role] = spec


def resolve_agent(role: str) -> AgentSpec:
    """Retourne un agent depuis le registre dynamique.

    La résolution initiale dépend désormais exclusivement de la DB via
    core.agents.recruiter.recruit(). Ici on ne fait que renvoyer les agents
    déjà instanciés pendant l'exécution.
    """
    if role in _DYNAMIC_REGISTRY:
        return _DYNAMIC_REGISTRY[role]
    raise KeyError(role)


# Compat: ancienne API qui chargeait un registre statique par défaut
def load_default_registry() -> Dict[str, AgentSpec]:  # pragma: no cover (compat)
    return dict(_DYNAMIC_REGISTRY)


async def get_agent_matrix(session: AsyncSession) -> Dict[str, Any]:
    """
    Lit la matrice des modèles depuis la DB et la retourne sous la forme:
      {"role:domain": models_dict, ...}
    """
    stmt = select(AgentModelsMatrix).where(AgentModelsMatrix.is_active == True).order_by(  # noqa: E712
        AgentModelsMatrix.created_at.desc()
    )
    res = await session.execute(stmt)
    rows = res.scalars().all()
    out: Dict[str, Any] = {}
    for r in rows:
        key = f"{r.role}:{r.domain}"
        if key not in out:
            out[key] = r.models or {}
    return out


async def ensure_seed_if_empty(session: AsyncSession) -> None:
    """Dev only: si tables vides, lance le seed initial.

    - Ne fait rien si APP_ENV/SENTRY_ENV=prod.
    - Idempotent: uniquement si aucune entrée dans AgentTemplate/AgentModelsMatrix.
    """
    env = os.getenv("APP_ENV") or os.getenv("SENTRY_ENV") or "dev"
    if str(env).lower() == "prod":
        return

    tpl_count = (await session.execute(select(AgentTemplate))).scalars().first()
    mm_count = (await session.execute(select(AgentModelsMatrix))).scalars().first()
    if tpl_count or mm_count:
        return

    try:
        log.info("agents: DB vide, seed initial (dev)")
        # Import tardif pour éviter les dépendances cycliques
        from scripts.seed_agents import seed_templates, seed_matrix  # type: ignore

        # Utilise les chemins par défaut (dossier seeds/)
        await seed_matrix()
        await seed_templates()
    except Exception as e:  # pragma: no cover — meilleure-effort dev only
        log.warning("seed agents échoué: %s", e)
