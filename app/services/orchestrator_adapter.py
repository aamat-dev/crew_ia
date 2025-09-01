from __future__ import annotations

import uuid
from typing import Any, Dict


async def start(plan_id: uuid.UUID, dry_run: bool = False) -> uuid.UUID:
    """Démarre un plan via l'orchestrateur.

    Cette implémentation simplifiée se contente de générer et retourner un
    identifiant de run aléatoire. L'orchestrateur réel se chargerait de
    l'exécution asynchrone du plan.
    """

    return uuid.uuid4()


async def node_action(
    node_id: uuid.UUID, action: str, payload: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Applique une action sur un nœud.

    On retourne le statut après action (ici l'action elle-même) et un indicateur
    `sidecar_updated` si un override de prompt ou de paramètres est présent.
    """

    sidecar_updated = bool(payload) and bool(
        (
            payload.get("override_prompt")
            or payload.get("prompt")
            or payload.get("params")
        )
    )
    return {"status_after": action, "sidecar_updated": sidecar_updated}
