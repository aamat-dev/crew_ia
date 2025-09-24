import asyncio
import json
import os
import uuid
from typing import Any

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager


async def main() -> None:
    # Active un fallback de plan draft en dev (voir backend/app/services/supervisor.py)
    os.environ.setdefault("PLAN_FALLBACK_DRAFT", "1")

    # Importe l'app FastAPI
    from backend.api.fastapi_app.app import app

    api_key = os.getenv("API_KEY", "test-key")
    req_id = f"verify-{uuid.uuid4().hex[:8]}"

    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            def h(extra: dict[str, str] | None = None) -> dict[str, str]:
                base = {"X-API-Key": api_key}
                if extra:
                    base.update(extra)
                return base

            # 1) Matrix supervisor (ollama)
            mx_payload = {
                "role": "supervisor",
                "domain": "general",
                "models": {"preferred": [{"provider": "ollama", "model": "llama3.1:8b"}]},
            }
            r = await ac.post("/agents/models-matrix", json=mx_payload, headers=h({"X-Request-ID": req_id, "X-Role": "admin"}))
            if r.status_code not in (201, 409):
                raise SystemExit(f"matrix create failed: {r.status_code} {r.text}")

            # 2) Template supervisor
            tpl_payload = {
                "name": "supervisor-general",
                "role": "supervisor",
                "domain": "general",
                "prompt_system": "Tu es un superviseur. Réponds uniquement en JSON conforme au schéma.",
                "default_model": "ollama:llama3.1:8b",
                "config": {},
            }
            r = await ac.post("/agents/templates", json=tpl_payload, headers=h({"X-Request-ID": req_id, "X-Role": "admin"}))
            if r.status_code not in (201, 409):
                raise SystemExit(f"template create failed: {r.status_code} {r.text}")

            # 3) Crée une tâche
            task_payload = {"title": f"Vérif plan via Supervisor {uuid.uuid4().hex[:6]}"}
            r = await ac.post("/tasks", json=task_payload, headers=h())
            r.raise_for_status()
            task = r.json()
            task_id = task["id"]
            print(json.dumps({"task": task}, ensure_ascii=False))

            # 4) Génère un plan (fallback draft actif)
            r = await ac.post(f"/tasks/{task_id}/plan", headers=h({"X-Request-ID": f"plan-{uuid.uuid4().hex[:6]}"}))
            r.raise_for_status()
            plan = r.json()
            plan_id = plan["plan_id"]
            status = plan["status"]
            print(json.dumps({"plan": plan}, ensure_ascii=False))

            # 5) Si draft, valider -> ready
            if status == "draft":
                r = await ac.post(
                    f"/plans/{plan_id}/submit_for_validation",
                    json={"validated": True, "errors": []},
                    headers=h({"X-Request-ID": f"val-{uuid.uuid4().hex[:6]}"}),
                )
                r.raise_for_status()
                print(json.dumps({"validation": r.json()}, ensure_ascii=False))

            # 6) Démarre
            r = await ac.post(f"/tasks/{task_id}/start", headers=h())
            r.raise_for_status()
            started = r.json()
            run_id = started["run_id"]
            print(json.dumps({"start": started}, ensure_ascii=False))

            # 7) Vérifie run
            r = await ac.get(f"/runs/{run_id}", headers=h())
            r.raise_for_status()
            print(json.dumps({"run": r.json()}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
