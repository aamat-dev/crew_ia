# core/storage/hooks.py
import json
from datetime import datetime, timezone
from core.storage.db_models import Run, Node, Artifact, Event, RunStatus, NodeStatus


async def on_run_start(storage, title: str, meta: dict | None = None) -> Run:
    run = Run(
        title=title,
        status=RunStatus.running,
        started_at=datetime.now(timezone.utc),
        meta=meta,
    )
    return await storage.save_run(run)


async def on_run_end(storage, run: Run, status: RunStatus):
    run.status = status
    run.ended_at = datetime.now(timezone.utc)
    return await storage.save_run(run)


async def on_node_start(storage, run_id, key, title, deps=None, checksum=None) -> Node:
    node = Node(
        run_id=run_id,
        key=key,
        title=title,
        status=NodeStatus.running,
        deps=list(deps or []),
        checksum=checksum,
    )
    return await storage.save_node(node)


async def on_node_end(storage, node: Node, status: NodeStatus):
    node.status = status
    node.updated_at = datetime.now(timezone.utc)
    return await storage.save_node(node)


async def on_artifact(storage, node_id, type_, path, summary=None, content=None):
    art = Artifact(
        node_id=node_id,
        type=type_,
        path=path,
        summary=summary,
        content=content,
    )
    return await storage.save_artifact(art)


async def log(storage, level: str, message: str, run_id=None, node_id=None, extra=None):
    if extra is not None:
        try:
            message = json.dumps({"message": message, "extra": extra}, ensure_ascii=False)
        except Exception:
            message = f"{message} | extra={extra}"
    evt = Event(run_id=run_id, node_id=node_id, level=level, message=message)
    return await storage.save_event(evt)
