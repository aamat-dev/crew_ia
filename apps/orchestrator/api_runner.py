from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from core.storage.composite_adapter import CompositeAdapter
from core.storage.db_models import Run, RunStatus, Node, NodeStatus, Artifact
from core.events.publisher import EventPublisher
from core.events.types import EventType
import logging
log = logging.getLogger("orchestrator.api_runner")

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
        # 1) Créer le node (running) AVANT d’émettre l’event NODE_STARTED (FK DB)
        node_uuid = uuid4()
        node = Node(
            id=node_uuid,
            run_id=run_uuid,
            key="n1",
            title="Node 1",
            status=NodeStatus.running,   # running d’abord
            created_at=started,
            updated_at=started,
            # checksum éventuel si NOT NULL dans ton schéma : ex. checksum=""
        )
        await writer.save_node(node=node)  # -> row présente en DB
        await event_publisher.emit(
            EventType.NODE_STARTED, {"run_id": run_id, "node_id": str(node_uuid)}
        )
        art_id = uuid4()
        artifact = Artifact(
            id=art_id,
            node_id=node_uuid,
            # ⚠️ mets ici une valeur 100% compatible avec ton Enum DB
            # (remplace "markdown" par la valeur exacte si ton Enum est différent)
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

        # 2) Clore proprement le node (completed) puis le run
        ended = dt.datetime.now(dt.timezone.utc)
        node.status = NodeStatus.completed
        node.updated_at = ended
        await writer.save_node(node=node)
        
        await writer.save_run(
            run=Run(id=run_uuid, title=title, status=RunStatus.completed, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(EventType.RUN_COMPLETED, {"run_id": run_id})
    except Exception as e:  # pragma: no cover
        log.exception("Background run failed for run_id=%s", run_id)
        ended = dt.datetime.now(dt.timezone.utc)
        await writer.save_run(
            run=Run(id=run_uuid, title=title, status=RunStatus.failed, started_at=started, ended_at=ended)
        )
        await event_publisher.emit(
            EventType.RUN_FAILED,
            {
                "run_id": run_id,
                "error_class": e.__class__.__name__,
                "message": str(e),
            },
        )
