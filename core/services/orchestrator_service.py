from __future__ import annotations

from uuid import uuid4, UUID
from typing import Any

from core.events.publisher import EventPublisher
from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Run, RunStatus
from apps.orchestrator.api_runner import run_task


async def schedule_run(task_spec: dict, options: Any, *, app_state, title: str | None = None) -> UUID:
    """Create a run entry and schedule its execution."""
    run_id = uuid4()
    title = title or task_spec.get("title") or "Adhoc run"
    storage: CompositeAdapter = app_state.storage
    await storage.save_run(
        run=Run(id=run_id, title=title, status=RunStatus.pending, started_at=None, ended_at=None)
    )

    task_group = app_state.task_group
    event_publisher: EventPublisher = app_state.event_publisher
    task_group.start_soon(
        run_task,
        str(run_id),
        task_spec,
        options,
        storage,
        event_publisher,
        title,
    )
    return run_id
