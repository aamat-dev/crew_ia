from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from .registry import AgentSpec, register_agent, ensure_seed_if_empty
from backend.api.fastapi_app.models.agent import AgentTemplate, AgentModelsMatrix


log = logging.getLogger(__name__)


def _role_to_db(role: str) -> list[tuple[str, str]]:
    """Mappe un rôle "humain" vers des (role, domain) DB candidats.

    Exemples:
      - Writer_FR -> [(executor, writer-translator)]
      - Researcher -> [(executor, research)]
      - Reviewer -> [(reviewer, general)]
      - Manager_Generic -> [(manager, frontend), (manager, backend)]
      - Supervisor -> [(supervisor, general)]
    """
    r = (role or "").strip().lower()
    if r.startswith("writer"):
        return [("executor", "writer-translator")]
    if r.startswith("research"):
        return [("executor", "research")]
    if r.startswith("review"):
        return [("reviewer", "general")]
    if r.startswith("manager"):
        return [("manager", "frontend"), ("manager", "backend"), ("manager", "general")]
    if r.startswith("supervisor"):
        return [("supervisor", "general")]
    # défaut: executor/général
    return [("executor", "general")]


def _pick_model(models: Dict[str, Any] | None) -> Optional[str]:
    if not isinstance(models, dict):
        return None
    prefs = (models or {}).get("preferred") or []
    fallbacks = (models or {}).get("fallbacks") or []
    if prefs:
        p = prefs[0]
        return f"{p.get('provider')}:{p.get('model')}"
    if fallbacks:
        p = fallbacks[0]
        return f"{p.get('provider')}:{p.get('model')}"
    return None


async def arecruit(role: str) -> AgentSpec:
    """
    Recrute un agent à partir de la DB (templates + matrice modèles)
    et l'enregistre dans le registre dynamique.
    """
    # Crée un sessionmaker local basé sur DATABASE_URL (iso des dépendances FastAPI)
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://crew:crew@localhost:5432/crew")
    try:
        engine = create_async_engine(database_url, pool_pre_ping=True, poolclass=NullPool)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    except Exception as e:
        # Fallback tests/unit sans DB
        log.warning("recruit: connexion DB impossible (%s), fallback minimal 'other'", e)
        spec = AgentSpec(role=role, system_prompt=None, provider="other", model="other", tools=[])
        register_agent(spec)
        return spec

    async with SessionLocal() as session:  # type: AsyncSession
        # Dev only: seed auto si vide
        try:
            await ensure_seed_if_empty(session)
        except Exception:
            log.debug("ensure_seed_if_empty échoué ou ignoré (dev)")

        # Trouve un template et une matrice selon les candidats
        tpl: AgentTemplate | None = None
        models_dict: Dict[str, Any] | None = None
        db_role = None
        db_domain = None
        for r, d in _role_to_db(role):
            # Template
            t_stmt = (
                select(AgentTemplate)
                .where(
                    AgentTemplate.role == r,
                    AgentTemplate.domain == d,
                    AgentTemplate.is_active == True,  # noqa: E712
                )
                .order_by(AgentTemplate.created_at.desc())
            )
            tpl = (await session.execute(t_stmt)).scalars().first()
            # Matrice
            m_stmt = (
                select(AgentModelsMatrix)
                .where(
                    AgentModelsMatrix.role == r,
                    AgentModelsMatrix.domain == d,
                    AgentModelsMatrix.is_active == True,  # noqa: E712
                )
                .order_by(AgentModelsMatrix.created_at.desc())
            )
            mm = (await session.execute(m_stmt)).scalars().first()
            models_dict = mm.models if mm else None
            if tpl or models_dict:
                db_role, db_domain = r, d
                break

        # Compose provider/model
        chosen = _pick_model(models_dict)
        provider = ""
        model = ""
        if chosen and ":" in chosen:
            provider, model = chosen.split(":", 1)
        elif tpl and tpl.default_model and ":" in tpl.default_model:
            provider, model = tpl.default_model.split(":", 1)

        # Prompt et outils
        system_prompt = None
        tools: list[str] = []
        if tpl:
            system_prompt = (tpl.prompt_system or "").format(language="fr", tone="professionnel")
            cfg = dict(tpl.config or {})
            capabilities = cfg.get("capabilities") or {}
            raw_tools = capabilities.get("tools") or []
            if isinstance(raw_tools, list):
                tools = [str(x) for x in raw_tools]

        spec = AgentSpec(role=role, system_prompt=system_prompt, provider=provider or "other", model=model or "other", tools=tools)

        # Mémorise dans le registre dynamique
        register_agent(spec)
        log.debug("recruit: role=%s -> db=(%s,%s) provider=%s model=%s", role, db_role, db_domain, spec.provider, spec.model)

        return spec


async def recruit(role: str) -> AgentSpec:
    """Version asynchrone principale (compat avec tests async)."""
    return await arecruit(role)


def recruit_sync(role: str) -> AgentSpec:
    """Compat synchro (si jamais requis par d'anciens tests)."""
    return asyncio.run(arecruit(role))
