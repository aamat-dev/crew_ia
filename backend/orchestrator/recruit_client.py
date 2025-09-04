from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
RECRUITER_ROLE = os.getenv("RECRUITER_ROLE", "editor")


async def recruit_agent(request_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Appelle l'API pour recruter un agent.

    Trois tentatives avec backoff 0.5/1/2s sont effectuées sur les erreurs 5xx.
    Les en-têtes ``X-Request-ID``, ``X-API-Key`` et ``X-Role`` sont propagés si définis.
    """
    delays = [0.0, 0.5, 1.0, 2.0]
    headers = {"X-Request-ID": request_id}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    if RECRUITER_ROLE:
        headers["X-Role"] = RECRUITER_ROLE
    async with httpx.AsyncClient(timeout=5.0) as client:
        for delay in delays:
            if delay:
                await asyncio.sleep(delay)
            resp = await client.post(f"{API_BASE}/agents/recruit", json=payload, headers=headers)
            if resp.status_code >= 500:
                continue
            resp.raise_for_status()
            return resp.json()
    resp.raise_for_status()
