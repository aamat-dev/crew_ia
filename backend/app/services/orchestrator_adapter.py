from __future__ import annotations

import os
import uuid
import logging
from typing import Any, Dict

from fastapi import HTTPException

from core.storage.file_adapter import FileAdapter
from core.storage.postgres_adapter import PostgresAdapter
from core.storage.composite_adapter import CompositeAdapter
from sqlalchemy.engine import make_url

from backend.orchestrator.service import OrchestratorService

log = logging.getLogger(__name__)


def _build_storage() -> CompositeAdapter:
    """Construit un CompositeAdapter aligné avec l'API (file + pg selon env)."""
    order = (os.getenv("STORAGE_ORDER") or "file,pg").replace(" ", "")
    runs_root = os.getenv("RUNS_ROOT") or ".runs"

    adapters = []
    for item in order.split(","):
        if not item:
            continue
        if item == "file":
            adapters.append(FileAdapter(base_dir=runs_root))
        elif item == "pg":
            try:
                db_url = os.getenv("DATABASE_URL")
                if not db_url:
                    continue
                if make_url(db_url).get_backend_name() == "postgresql":
                    adapters.append(PostgresAdapter(db_url))
            except Exception:
                # Tolérant: si la configuration DB est invalide, on se contente du stockage fichier
                log.debug("orchestrator_adapter: PostgresAdapter non initialisé", exc_info=True)
                continue
        else:
            raise RuntimeError(f"Unknown adapter in STORAGE_ORDER: {item}")
    if not adapters:
        adapters.append(FileAdapter(base_dir=runs_root))
    return CompositeAdapter(adapters)


async def start(plan_id: uuid.UUID, dry_run: bool = False) -> uuid.UUID:
    """Démarre réellement un plan via l'orchestrateur.

    - Passe le Run à running et crée les nœuds en DB selon le plan
    - Publie les événements (RUN_STARTED, puis NODE_* et finalisation)
    - Exécute en tâche de fond (non bloquant)
    """
    storage = _build_storage()
    service = OrchestratorService(storage)
    run_id_str = await service.start(str(plan_id), dry_run=dry_run)
    try:
        return uuid.UUID(run_id_str)
    except Exception:
        # Par robustesse, renvoie un UUID aléatoire si le service retourne un identifiant non-UUID
        log.warning("orchestrator_service returned non-UUID run id: %s", run_id_str)
        return uuid.uuid4()


# État simulé des nœuds pour vérifier les transitions.
_NODE_STATES: Dict[uuid.UUID, Dict[str, Any]] = {}


async def node_action(
    node_id: uuid.UUID, action: str, payload: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Applique une action sur un nœud (mock en mémoire).

    - Valide les transitions et lève HTTP 409 si invalide
    - Retourne le statut après action
    - Indique si le sidecar LLM a été mis à jour (override prompt/params)
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
