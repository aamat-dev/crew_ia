from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from uuid import uuid4
from datetime import datetime, timezone

from ..schemas.prompting import RecruitRequest, RecruitResponse
from ..models.agent import Agent, AgentTemplate, AgentModelsMatrix


class RecruitService:
    @staticmethod
    async def recruit(session: AsyncSession, payload: RecruitRequest, request_id: str) -> RecruitResponse:
        """
        Recrute un agent SANS appel HTTP sortant.
        Sélectionne un template (role/domain), choisit un modèle via la matrice,
        instancie l'Agent et renvoie un sidecar expliquant la décision.
        """
        role = payload.role or "executor"
        domain = payload.domain or "general"

        # 1) Trouver un template (role/domain)
        tpl_stmt = (
            select(AgentTemplate)
            .where(AgentTemplate.role == role, AgentTemplate.domain == domain, AgentTemplate.is_active == True)  # noqa: E712
            .order_by(AgentTemplate.created_at.desc())
        )
        tpl = (await session.execute(tpl_stmt)).scalars().first()

        # 2) Trouver une matrice (role/domain) pour choisir modèle/provider
        mm_stmt = (
            select(AgentModelsMatrix)
            .where(
                AgentModelsMatrix.role == role,
                AgentModelsMatrix.domain == domain,
                AgentModelsMatrix.is_active == True,
            )  # noqa: E712
            .order_by(AgentModelsMatrix.created_at.desc())
        )
        mm = (await session.execute(mm_stmt)).scalars().first()

        # Sélection simple : premier "preferred", sinon premier "fallback"
        chosen_model = None
        if mm and isinstance(mm.models, dict):
            prefs = (mm.models or {}).get("preferred") or []
            fallbacks = (mm.models or {}).get("fallbacks") or []
            if prefs:
                chosen_model = f"{prefs[0].get('provider')}:{prefs[0].get('model')}"
            elif fallbacks:
                chosen_model = f"{fallbacks[0].get('provider')}:{fallbacks[0].get('model')}"

        # 3) Construire prompts et config à partir du template
        prompt_system = None
        default_model = chosen_model
        config = {}
        template_used = None
        if tpl:
            template_used = tpl.name
            prompt_system = (tpl.prompt_system or "").format(
                language=payload.language or "fr",
                tone=payload.tone or "professionnel",
            )
            default_model = default_model or tpl.default_model
            config = dict(tpl.config or {})

        # 4) Instancier l'agent (name unique simple)
        #    Ex: "recruit-executor-writer-translator-<uuid4>"
        safe_domain = (domain or "general").replace("/", "-")
        name = f"recruit-{role}-{safe_domain}-{uuid4().hex[:8]}"
        agent = Agent(
            name=name,
            role=role,
            domain=domain,
            prompt_system=prompt_system,
            default_model=default_model,
            config=config or {},
        )
        session.add(agent)
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            # Doublon probable (contrainte unique name+role+domain)
            raise HTTPException(status_code=409, detail="agent already exists") from e
        except Exception as e:
            # Laisse les erreurs inattendues remonter sous forme 500 via handler unifié
            await session.rollback()
            from core.exceptions import PersistenceError
            raise PersistenceError("failed to persist agent") from e
        await session.refresh(agent)

        # 5) Sidecar explicable
        sidecar = {
            "_kind": "recruitment_decision",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "role_description": payload.role_description,
                "role": role,
                "domain": domain,
                "language": payload.language,
                "tone": payload.tone,
                "tools_required": payload.tools_required,
                "budget": payload.budget,
                "latency_target_ms": payload.latency_target_ms,
                "safety_level": payload.safety_level,
            },
            "selection": {
                "template_used": template_used,
                "chosen_model": default_model,
                "source": "models_matrix" if mm else "template_default_or_none",
            },
            "constraints": {
                "rbac": "enforced if FEATURE_RBAC=true",
                "request_id_required": True,
            },
        }

        return RecruitResponse(
            agent_id=str(agent.id),
            id=str(agent.id),
            name=agent.name,
            role=agent.role,
            domain=agent.domain,
            default_model=agent.default_model,
            sidecar=sidecar,
            template_used=template_used,
            template_id=str(tpl.id) if tpl else None,
            created_at=agent.created_at,
        )
