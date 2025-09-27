from __future__ import annotations

import os
import uuid
import logging
from typing import Any, Dict
from datetime import datetime, timezone

from fastapi import HTTPException

from core.storage.file_adapter import FileAdapter
from core.storage.postgres_adapter import PostgresAdapter
from core.storage.composite_adapter import CompositeAdapter
from sqlalchemy.engine import make_url

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import select
from core.storage.db_models import Node, NodeStatus, Event  # type: ignore

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
    if run_id_str:
        _RUN_SERVICES[run_id_str] = service
    try:
        return uuid.UUID(run_id_str)
    except Exception:
        # Par robustesse, renvoie un UUID aléatoire si le service retourne un identifiant non-UUID
        log.warning("orchestrator_service returned non-UUID run id: %s", run_id_str)
    return uuid.uuid4()


async def cancel(run_id: uuid.UUID) -> bool:
    """Annule un run en cours s'il a été démarré via OrchestratorService.

    Retourne True si une propagation a été effectuée, False sinon (DB-only).
    """
    svc = _RUN_SERVICES.get(str(run_id))
    if not svc:
        return False
    try:
        await svc.cancel()
        return True
    finally:
        # Libère la référence pour éviter les fuites
        _RUN_SERVICES.pop(str(run_id), None)


async def pause(run_id: uuid.UUID) -> bool:
    svc = _RUN_SERVICES.get(str(run_id))
    if not svc:
        return False
    await svc.pause()
    return True


async def resume(run_id: uuid.UUID) -> bool:
    svc = _RUN_SERVICES.get(str(run_id))
    if not svc:
        return False
    await svc.resume()
    return True


# État simulé des nœuds pour vérifier les transitions.
_NODE_STATES: Dict[uuid.UUID, Dict[str, Any]] = {}


async def _node_action_db(node_id: uuid.UUID, action: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    """Essaie d'appliquer l'action en base (si PostgreSQL configuré et nœud présent).

    Retourne un dict résultat si traité côté DB, sinon None pour laisser le fallback mémoire.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    try:
        engine = create_async_engine(db_url, pool_pre_ping=True, poolclass=NullPool)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    except Exception:
        return None

    async with SessionLocal() as session:
        node = await session.get(Node, node_id)
        if not node:
            return None

        now = datetime.now(timezone.utc)
        current = str(getattr(node, "status", ""))
        status_after: str | None = None

        # Applique des transitions minimales compatibles avec l'ENUM
        if action == "pause":
            # Conserve l'état courant en DB, mais émet un évènement
            await session.merge(Event(run_id=node.run_id, node_id=node.id, level="NODE_PAUSED", message="{}", timestamp=now))
            await session.commit()
            return {"status_after": current}
        elif action == "resume":
            # Reprise (DB inchangée), mais trace l'évènement
            await session.merge(Event(run_id=node.run_id, node_id=node.id, level="NODE_RESUMED", message="{}", timestamp=now))
            await session.commit()
            return {"status_after": "running"}
        elif action == "skip":
            # Termine le nœud sans exécuter (completed en DB pour compat ENUM)
            node.status = NodeStatus.completed
            node.updated_at = now
            await session.merge(node)
            await session.merge(Event(run_id=node.run_id, node_id=node.id, level="NODE_SKIPPED", message="{}", timestamp=now))
            await session.commit()
            return {"status_after": "completed"}
        elif action == "override":
            # Ré-enfile le nœud (queued) et note le prompt/params
            node.status = NodeStatus.queued
            node.updated_at = now
            await session.merge(node)
            msg = {k: v for k, v in payload.items() if k in {"prompt", "params"}}
            await session.merge(Event(run_id=node.run_id, node_id=node.id, level="NODE_OVERRIDDEN", message=(msg and __import__('json').dumps(msg)) or "{}", timestamp=now))
            await session.commit()
            return {"status_after": "queued", "sidecar_updated": bool(msg) or None}
        else:
            raise HTTPException(status_code=400, detail="unknown action")

    return None


async def node_action(
    node_id: uuid.UUID, action: str, payload: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Applique une action sur un nœud (mock en mémoire).

    - Valide les transitions et lève HTTP 409 si invalide
    - Retourne le statut après action
    - Indique si le sidecar LLM a été mis à jour (override prompt/params)
    """
    payload = payload or {}

    # 1) Essaye d'abord en base (si le nœud existe)
    db_res = await _node_action_db(node_id, action, payload)
    if db_res is not None:
        # DB a pris en charge; complète le champ sidecar_updated si absent
        if action == "override":
            db_res.setdefault("sidecar_updated", bool(payload.get("prompt") or payload.get("params")) or None)
        return {"node_id": node_id, **db_res}

    # 2) Fallback mémoire (par défaut: 'running')
    state = _NODE_STATES.setdefault(node_id, {"status": "running", "run_id": uuid.uuid4()})
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
    return {"status_after": status_after, "sidecar_updated": sidecar_updated or None, "run_id": state["run_id"]}
_RUN_SERVICES: Dict[str, OrchestratorService] = {}
