#!/usr/bin/env python3
"""
Script utilitaire pour créer une tâche via l'API, générer son plan,
simuler une validation humaine, assigner deux nœuds puis démarrer le run.

Variables d'environnement utilisées :
- API_URL (défaut : http://localhost:8000)
- API_KEY (obligatoire)
- DRY_RUN (défaut : true)
"""

import os
import sys
import uuid
import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}

if not API_KEY:
    print("API_KEY manquante", file=sys.stderr)
    sys.exit(1)

request_id = str(uuid.uuid4())

headers = {
    "X-API-Key": API_KEY,
    "X-Request-ID": request_id,
}

with httpx.Client(base_url=API_URL, headers=headers, timeout=10.0) as client:
    # Création de la tâche brouillon
    r = client.post("/tasks", json={"title": "Demo"})
    r.raise_for_status()
    task_id = r.json()["id"]
    request_id = r.headers.get("X-Request-ID", request_id)
    print(f"tâche créée: {task_id} (X-Request-ID={request_id})")

    client.headers["X-Request-ID"] = request_id

    # Première génération du plan
    r = client.post(f"/tasks/{task_id}/plan")
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    body = r.json()
    plan_id = body["plan_id"]
    status = body.get("status")
    nodes = [n["id"] for n in body["graph"]["plan"]]
    if len(nodes) < 2:
        print("Plan insuffisant pour l'assignation (au moins deux nœuds requis)", file=sys.stderr)
        sys.exit(1)
    print(
        f"plan généré: {plan_id} (status={status}) avec nœuds {nodes[:2]} (X-Request-ID={request_id})"
    )

    client.headers["X-Request-ID"] = request_id

    # Soumission pour validation (rejet simulé)
    r = client.post(
        f"/plans/{plan_id}/submit_for_validation",
        json={"validated": False, "errors": ["ajuster scope"]},
    )
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    print(f"plan {plan_id} soumis pour validation (rejeté) (X-Request-ID={request_id})")

    client.headers["X-Request-ID"] = request_id

    # Régénération du plan
    r = client.post(f"/tasks/{task_id}/plan")
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    body = r.json()
    plan_id = body["plan_id"]
    status = body.get("status")
    nodes = [n["id"] for n in body["graph"]["plan"]]
    if len(nodes) < 2:
        print("Plan insuffisant pour l'assignation (au moins deux nœuds requis)", file=sys.stderr)
        sys.exit(1)
    print(
        f"plan régénéré: {plan_id} (status={status}) avec nœuds {nodes[:2]} (X-Request-ID={request_id})"
    )

    client.headers["X-Request-ID"] = request_id

    # Validation finale
    r = client.post(f"/plans/{plan_id}/submit_for_validation", json={"validated": True})
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    print(f"plan {plan_id} validé (X-Request-ID={request_id})")

    client.headers["X-Request-ID"] = request_id

    # Assignation de deux nœuds
    payload = {
        "items": [
            {
                "node_id": nodes[0],
                "role": "writer",
                "agent_id": "agent-1",
                "llm_backend": "openai",
                "llm_model": "gpt-4o-mini",
            },
            {
                "node_id": nodes[1],
                "role": "reviewer",
                "agent_id": "agent-2",
                "llm_backend": "openai",
                "llm_model": "gpt-4o-mini",
            },
        ]
    }
    r = client.post(f"/plans/{plan_id}/assignments", json=payload)
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    print(
        f"assignations appliquées: {r.json().get('updated', 0)} mises à jour (X-Request-ID={request_id})"
    )

    client.headers["X-Request-ID"] = request_id

    # Démarrage du run (paramètre dry_run respecté)
    r = client.post(f"/tasks/{task_id}/start", params={"dry_run": str(DRY_RUN).lower()})
    r.raise_for_status()
    request_id = r.headers.get("X-Request-ID", request_id)
    run_id = r.json()["run_id"]
    location = r.headers.get("Location")
    print(
        f"run démarré: {run_id} (dry_run={r.json()['dry_run']}) (X-Request-ID={request_id})"
    )
    if location:
        print(f"Location: {location}")
