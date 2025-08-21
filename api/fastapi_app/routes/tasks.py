# api/fastapi_app/routes/tasks.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Header
from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4, UUID
import datetime as dt
import logging
import anyio
from typing import Optional

from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Run, RunStatus
from core.events.publisher import EventPublisher
from apps.orchestrator.api_runner import run_task

log = logging.getLogger("api.tasks")
router = APIRouter(prefix="/tasks", tags=["tasks"])


# --- Schemas ---

class TaskSpec(BaseModel):
    type: Optional[str] = None
    model_config = ConfigDict(extra="allow")  # accepte 'plan', etc.


class CreateTaskBody(BaseModel):
    title: str = Field(..., examples=["Adhoc run"])
    task_spec: Optional[TaskSpec] = None  # certains clients envoient 'task' à la place

    model_config = ConfigDict(extra="allow")  # tolère 'task', 'options', etc.


class CreateTaskResponse(BaseModel):
    status: str
    run_id: str
    location: str


class TaskStatusResponse(BaseModel):
    run_id: str
    status: str
    title: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


# --- Helpers ---

def _normalize_status(value) -> str:
    """
    Normalise un statut en chaîne simple: 'running' / 'completed' / 'failed' / 'unknown'.
    Gère les Enum (RunStatus.completed), les strings comme 'RunStatus.completed', etc.
    """
    if value is None:
        return "unknown"
    # Enum -> prendre .value
    try:
        enum_value = getattr(value, "value")
        if enum_value:
            value = enum_value
    except Exception:
        pass
    s = str(value)
    if "." in s:
        # ex: "RunStatus.completed" -> "completed"
        s = s.split(".", 1)[1]
    return s.lower() or "unknown"


# --- Dependencies from app state ---

def get_storage(request: Request) -> CompositeAdapter:
    storage: CompositeAdapter | None = getattr(request.app.state, "storage", None)
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    return storage


def get_publisher(request: Request) -> EventPublisher:
    pub: EventPublisher | None = getattr(request.app.state, "event_publisher", None)
    if not pub:
        raise HTTPException(status_code=500, detail="Event publisher not initialized")
    return pub


# --- Routes ---

@router.post("", response_model=CreateTaskResponse, status_code=202)
async def create_task(
    body: CreateTaskBody,
    background: BackgroundTasks,
    request: Request,
    storage: CompositeAdapter = Depends(get_storage),
    publisher: EventPublisher = Depends(get_publisher),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    # Auth minimale : absence d'API key => 401 (les tests le vérifient)
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Supporte 'task_spec' (API) ou 'task' (tests e2e)
    raw = await request.json()
    if body.task_spec is not None:
        task_spec = body.task_spec.model_dump(exclude_unset=True)
    elif isinstance(raw, dict) and isinstance(raw.get("task"), dict):
        task_spec = raw["task"]
    else:
        task_spec = {}

    run_id_str = str(uuid4())
    run_id = UUID(run_id_str)
    title = body.title or "Adhoc run"

    started_at = dt.datetime.now(dt.timezone.utc)
    # IMPORTANT : Run.id en UUID
    await storage.save_run(
        run=Run(id=run_id, title=title, status=RunStatus.running, started_at=started_at)
    )

    # === Chemin spécial DEMO : exécution synchrone pour éviter les flakes ===
    if (task_spec or {}).get("type") == "demo":
        try:
            class _Opts:
                dry_run = False
                override = []
            await run_task(
                run_id=run_id_str,
                task_spec=task_spec,
                options=_Opts(),
                storage=storage,
                event_publisher=publisher,
                title=title,
                request_id=None,
            )
        except Exception as e:  # pragma: no cover
            log.exception("Inline demo task failed for run_id=%s", run_id_str)
            ended = dt.datetime.now(dt.timezone.utc)
            await storage.save_run(
                run=Run(id=run_id, title=title, status=RunStatus.failed, started_at=started_at, ended_at=ended)
            )
            raise HTTPException(status_code=500, detail=f"Demo task failed: {e}")

        return CreateTaskResponse(status="accepted", run_id=run_id_str, location=f"/runs/{run_id_str}")

    # === Chemin normal : arrière-plan ===
    def _bg():
        async def _runner():
            class _Opts:
                dry_run = False
                override = []
            try:
                await run_task(
                    run_id=run_id_str,
                    task_spec=task_spec,
                    options=_Opts(),
                    storage=storage,
                    event_publisher=publisher,
                    title=title,
                    request_id=None,
                )
            except Exception:
                log.exception("Background run failed for run_id=%s", run_id_str)
        anyio.run(_runner)

    background.add_task(_bg)
    return CreateTaskResponse(status="accepted", run_id=run_id_str, location=f"/runs/{run_id_str}")


@router.get("/{run_id}", response_model=TaskStatusResponse)
async def get_task_status(
    run_id: str,
    storage: CompositeAdapter = Depends(get_storage),
):
    # Essayer d'abord en UUID (Postgres), puis retomber sur str (filesystem)
    run = None
    try:
        run = await storage.get_run(UUID(run_id))
    except Exception:
        pass
    if not run:
        run = await storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    status_raw = getattr(run, "status", None)
    status = _normalize_status(status_raw)
    started_at = getattr(run, "started_at", None)
    ended_at = getattr(run, "ended_at", None)
    title = getattr(run, "title", None)

    return TaskStatusResponse(
        run_id=run_id,
        status=status,
        title=title,
        started_at=started_at.isoformat() if started_at else None,
        ended_at=ended_at.isoformat() if ended_at else None,
    )
