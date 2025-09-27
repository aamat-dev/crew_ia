from __future__ import annotations

import os
from fastapi import APIRouter, Depends

from ..deps import strict_api_key_auth

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(strict_api_key_auth)])


@router.get("/llm")
async def get_llm_config() -> dict:
    """Expose une vue lecture des providers/modèles LLM depuis l'environnement.

    Strictement en lecture; utile pour l'UX (afficher la source LLM).
    """
    keys = [
        "LLM_DEFAULT_PROVIDER",
        "LLM_DEFAULT_MODEL",
        "SUPERVISOR_PROVIDER",
        "SUPERVISOR_MODEL",
        "MANAGER_PROVIDER",
        "MANAGER_MODEL",
        "EXECUTOR_PROVIDER",
        "EXECUTOR_MODEL",
        "RECRUITER_PROVIDER",
        "RECRUITER_MODEL",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "PLAN_FALLBACK_DRAFT",
    ]
    return {k: os.getenv(k) for k in keys}

