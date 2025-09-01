from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import HTTPException


async def start(plan_id: uuid.UUID, dry_run: bool = False) -> uuid.UUID:
    """Démarre un plan via l'orchestrateur.

    Cette implémentation simplifiée se contente de générer et retourner un
    identifiant de run aléatoire. L'orchestrateur réel se chargerait de
    l'exécution asynchrone du plan.
    """

    return uuid.uuid4()


# État simulé des nœuds pour vérifier les transitions.
_NODE_STATES: Dict[uuid.UUID, Dict[str, Any]] = {}


async def node_action(
    node_id: uuid.UUID, action: str, payload: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Applique une action sur un nœud.

    Cette implémentation mémoire maintient un état minimal afin de vérifier la
    cohérence des transitions. En cas de transition invalide, on lève une
    ``HTTPException`` 409.

    On retourne le statut après action et un indicateur ``sidecar_updated`` si
    un override de prompt ou de paramètres est présent.
    """

    payload = payload or {}

    state = _NODE_STATES.setdefault(
        node_id, {"status": "running", "run_id": uuid.uuid4()}
    )
    current = state["status"]

    if action == "pause":
        if current != "running":
            raise HTTPException(status_code=409, detail="invalid transition")
        state["status"] = "paused"
        status_after = "paused"
    elif action == "resume":
        if current != "paused":
            raise HTTPException(status_code=409, detail="invalid transition")
        state["status"] = "running"
        status_after = "running"
    elif action == "skip":
        if current != "paused":
            raise HTTPException(status_code=409, detail="invalid transition")
        state["status"] = "skipped"
        status_after = "skipped"
    elif action == "override":
        if current not in {"running", "paused"}:
            raise HTTPException(status_code=409, detail="invalid transition")
        state["status"] = "queued"
        status_after = "queued"
    else:
        raise HTTPException(status_code=400, detail="unknown action")

    sidecar_updated = bool(payload.get("prompt") or payload.get("params"))
    return {
        "status_after": status_after,
        "sidecar_updated": sidecar_updated or None,
        "run_id": state["run_id"],
    }
