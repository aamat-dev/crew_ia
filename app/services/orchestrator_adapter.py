from __future__ import annotations

from typing import Any, Dict
from uuid import UUID


async def node_action(node_id: UUID, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Relay d'action vers l'orchestrateur.

    Cette fonction est un adaptateur asynchrone vers le service
    d'orchestration. L'implémentation réelle sera branchée ultérieurement.
    """
    raise NotImplementedError("orchestrator adapter not implemented")
