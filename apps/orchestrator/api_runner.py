from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Run, RunStatus, Node, NodeStatus, Artifact
from core.events.publisher import EventPublisher
from core.events.types import EventType


async def run_task(
    run_id: str,
    task_spec: dict,
    options: object,
    writer: CompositeAdapter,
    event_publisher: EventPublisher,
    title: str,
) -> None:
    run_uuid = UUID(run_id)
    started = dt.datetime.now(dt.timezone.utc)
    await writer.save_run(run=Run(id=run_uuid, title=title, status=RunStatus.running, started_at=started))
    await event_publisher.emit(EventType.RUN_STARTED, {"run_id": run_id, "title": title})

    try:
        node_uuid = uuid4()
        await event_publisher.emit(EventType.NODE_STARTED, {"run_id": run_id, "node_id": str(node_uuid)})
        node = Node(
            id=node_uuid,
            run_id=run_uuid,
            key="n1",
            title="Node 1",
            status=NodeStatus.completed,
            created_at=started,
            updated_at=started,
        )
        await writer.save_node(node=node)
        art_id = uuid4()
        artifact = Artifact(
            id=art_id,
            node_id=node_uuid,
            type="markdown",
            path="/tmp/demo.md",
            content="# demo\nHello",
            summary="demo",
            created_at=started,
        )
        await writer.save_artifact(artifact=artifact)
        await event_publisher.emit(
            EventType.NODE_COMPLETED,
            {"run_id": run_id, "node_id": str(node_uuid), "artifact_id": str(art_id)},
        )

        ended = dt.datetime.now(dt.timezone.utc)
        await writer.save_run(
            run=Run(id=run_uuid, title=title, status=RunStatus.completed, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(EventType.RUN_COMPLETED, {"run_id": run_id})
    except Exception as e:  # pragma: no cover
        ended = dt.datetime.now(dt.timezone.utc)
        await writer.save_run(
            run=Run(id=run_uuid, title=title, status=RunStatus.failed, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(
            EventType.RUN_FAILED,
            {"run_id": run_id, "error_class": e.__class__.__name__, "message": str(e)},
        )
