from __future__ import annotations

from uuid import UUID, uuid4


async def start(plan_id: UUID, dry_run: bool) -> UUID:
    """Démarre l'orchestrateur pour un ``plan_id`` donné.

    Cette implémentation minimale retourne simplement un ``run_id`` généré.
    """
    # TODO: brancher l'orchestrateur réel
    return uuid4()
