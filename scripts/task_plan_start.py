#!/usr/bin/env python3
"""
Script utilitaire pour créer une tâche via l'API, générer son plan,
assigner deux nœuds puis démarrer le run.

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
    req_id = r.headers.get("X-Request-ID", request_id)
    print(f"tâche créée: {task_id} (X-Request-ID={req_id})")

    # Propagation de l'ID de requête
    client.headers["X-Request-ID"] = req_id

    # Génération du plan
    r = client.post(f"/tasks/{task_id}/plan")
    r.raise_for_status()
    plan_id = r.json()["plan_id"]
    nodes = [n["id"] for n in r.json()["graph"]["plan"]]
    if len(nodes) < 2:
        print("Plan insuffisant pour l'assignation (au moins deux nœuds requis)", file=sys.stderr)
        sys.exit(1)
    print(f"plan généré: {plan_id} avec nœuds {nodes[:2]}")

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
    print(f"assignations appliquées: {r.json().get('updated', 0)} mises à jour")

    # Démarrage du run (dry_run param)
    r = client.post(f"/tasks/{task_id}/start", params={"dry_run": str(DRY_RUN).lower()})
    r.raise_for_status()
    run_id = r.json()["run_id"]
    print(f"run démarré: {run_id} (dry_run={r.json()['dry_run']})")
