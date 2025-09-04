from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from .recruit_client import recruit_agent

logger = logging.getLogger(__name__)


async def handle_missing_role(
    run_id: str,
    request_id: str,
    payload: Dict[str, Any],
    node: Dict[str, Any],
    runs_root: str | None = None,
) -> Dict[str, Any]:
    """Recrute un agent manquant et persiste le sidecar.

    Le ``agent_id`` renvoyé est injecté dans ``node``. Le sidecar JSON est
    stocké sous ``runs/<run_id>/sidecars/<request_id>.llm.json``.
    """
    logger.info("recruit_missing_role", extra={"X-Request-ID": request_id})
    result = await recruit_agent(request_id, payload)
    agent_id = result.get("agent_id")
    node["agent_id"] = agent_id
    sidecar = result.get("sidecar")

    root = runs_root or os.getenv("RUNS_ROOT", "runs")
    sidecar_dir = Path(root) / run_id / "sidecars"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = sidecar_dir / f"{request_id}.llm.json"
    with sidecar_path.open("w", encoding="utf-8") as f:
        json.dump(sidecar, f)
    logger.info("sidecar_written", extra={"X-Request-ID": request_id, "path": str(sidecar_path)})
    return node
