from __future__ import annotations

import json
from typing import Any, Dict
from uuid import UUID

from core.storage.composite_adapter import CompositeAdapter
from .types import EventType

import logging
log = logging.getLogger("events.publisher")


class EventPublisher:
    """Simple wrapper to persist structured events via a CompositeAdapter."""

    def __init__(self, adapter: CompositeAdapter):
        self.adapter = adapter
        self.disabled = False

    async def emit(
        self, event_type: EventType | str, payload: Dict[str, Any], request_id: str | None = None
    ):
        if self.disabled:
            return
        if request_id is not None:
            payload = {**payload, "request_id": request_id}

        level = event_type.value if isinstance(event_type, EventType) else str(event_type)
        run_id = payload.get("run_id")
        node_id = payload.get("node_id")
        try:
            if isinstance(run_id, str):
                run_id = UUID(run_id)
        except Exception:
            pass
        try:
            if isinstance(node_id, str):
                node_id = UUID(node_id)
        except Exception:
            pass
        message = json.dumps(payload, ensure_ascii=False)
        log.debug("emit %s: %s", level, message)
        await self.adapter.save_event(run_id=run_id, node_id=node_id, level=level, message=message)
