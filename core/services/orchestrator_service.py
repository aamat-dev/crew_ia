from __future__ import annotations
from uuid import uuid4, UUID
from typing import Any, Dict
import json
import os
import anyio
from datetime import datetime, timezone

from core.storage.db_models import Run, RunStatus
from core.storage.composite_adapter import CompositeAdapter
from core.storage.file_adapter import FileAdapter
from core.storage.postgres_adapter import PostgresAdapter
from core.events.publisher import EventPublisher
from apps.orchestrator.api_runner import run_task

def _load_task_from_file(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Task JSON not found: {path}")
    if not path.endswith(".json"):
        raise ValueError("task_file must be a JSON file")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "plan" not in data or not isinstance(data["plan"], list):
        raise ValueError("task_file JSON must contain a 'plan' array")
    return data

async def schedule_run(
    task_spec: Dict[str, Any] | None,
    options: Any,
    *,
    app_state,
    title: str | None = None,
    task_file: str | None = None,
    request_id: str | None = None,
) -> UUID:
    """
    - Génère un UUID de run
    - Enregistre Run(running)
    - Lance l'exécution en tâche de fond (AnyIO TaskGroup) via api_runner.run_task
    """
    run_id = uuid4()

    # Normalisation de la source du plan
    if task_spec is None and task_file:
        task_spec = _load_task_from_file(task_file)
    if task_spec is None:
        raise ValueError("Missing task_spec or task_file")

    # Titre
    title = title or task_spec.get("title") or "Adhoc run"

    # Récupération des singletons créés dans lifespan()
    storage: CompositeAdapter = getattr(app_state, "storage")
    event_publisher: EventPublisher = getattr(app_state, "event_publisher")
    tg = getattr(app_state, "task_group")

    # Créer une entrée Run (running)
    now = datetime.now(timezone.utc)
    await storage.save_run(
        run=Run(id=run_id, title=title, status=RunStatus.running, started_at=now, meta={"request_id": request_id})
    )

    # Démarrer l'exécution asynchrone fire-and-forget
    tg.start_soon(
        run_task,
        str(run_id),
        task_spec,
        options,
        storage,
        event_publisher,
        title,
        request_id,
    )

    # Laisser une opportunité d'ordonnancement (utile pour les tests)
    await anyio.sleep(0)
    return run_id
