from __future__ import annotations
import httpx
import os
from typing import Any, Dict, Optional

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY")

async def create_feedback(payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    if headers:
        h.update(headers)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE}/feedbacks", json=payload, headers=h)
        r.raise_for_status()
        return r.json()
