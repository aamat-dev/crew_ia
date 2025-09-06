from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Awaitable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.storage.db_models import Run, RunStatus, Node, NodeStatus, Event

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR") or ".runs")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_callbacks(
    session: AsyncSession, run_id: uuid.UUID, request_id: str | None
) -> tuple[
    Callable[[Any, str], Awaitable[None]],
    Callable[[Any, str, str], Awaitable[None]],
]:
    async def on_node_start(node: Any, node_key: str) -> None:
        now = utcnow()
        db_node = Node(
            run_id=run_id,
            key=node_key,
            title=getattr(node, "title", ""),
            status=NodeStatus.running,
            role=getattr(node, "suggested_agent_role", None),
            created_at=now,
            updated_at=now,
        )
        session.add(db_node)
        await session.flush()
        try:
            setattr(node, "db_id", db_node.id)
        except Exception:
            pass
        session.add(
            Event(
                run_id=run_id,
                node_id=db_node.id,
                level="NODE_STARTED",
                message="{}",
                request_id=request_id,
            )
        )
        await session.commit()

    async def on_node_end(node: Any, node_key: str, status: str) -> None:
        now = utcnow()
        node_id = getattr(node, "db_id", None)
        if node_id is None:
            res = await session.execute(
                select(Node.id).where(Node.run_id == run_id, Node.key == node_key)
            )
            node_id = res.scalar_one_or_none()
        node_obj = await session.get(Node, node_id) if node_id else None
        try:
            node_status = NodeStatus(status)
        except Exception:
            node_status = NodeStatus.failed
        if node_obj:
            node_obj.status = node_status
            node_obj.updated_at = now
        meta = {}
        node_dir = ARTIFACTS_DIR / str(run_id) / "nodes" / node_key
        if node_dir.is_dir():
            for p in node_dir.glob("*.llm.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                usage = data.get("usage") or {}
                usage.setdefault("completion_tokens", 0)
                data["usage"] = usage
                session.add(
                    Event(
                        run_id=run_id,
                        node_id=node_id,
                        level="LLM_METADATA",
                        message="llm metadata",
                        extra=data,
                        request_id=request_id,
                    )
                )
                if not meta:
                    meta = data
        payload = dict(meta)
        if request_id and "request_id" not in payload:
            payload["request_id"] = request_id
        session.add(
            Event(
                run_id=run_id,
                node_id=node_id,
                level="NODE_COMPLETED" if node_status == NodeStatus.completed else "NODE_FAILED",
                message=json.dumps(payload),
                request_id=request_id,
            )
        )
        await session.commit()

    return on_node_start, on_node_end


async def finalize_run(session: AsyncSession, run: Run, result: Any) -> None:
    status_val = (result or {}).get("status")
    if status_val in {"success", "completed", "ok", "done"}:
        run.status = RunStatus.completed
    else:
        run.status = RunStatus.failed
    run.ended_at = utcnow()
    session.add(run)
    await session.commit()
