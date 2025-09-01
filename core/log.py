from __future__ import annotations

import contextvars
import datetime as dt
import json
import logging
from typing import Any

# Context variables
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
run_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("run_id", default=None)
node_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("node_id", default=None)
status_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("status", default=None)
llm_backend_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("llm_backend", default=None)
llm_model_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("llm_model", default=None)

class ContextFilter(logging.Filter):
    """Injecte les contextvars dans chaque LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        record.request_id = request_id_var.get()
        record.run_id = run_id_var.get()
        record.node_id = node_id_var.get()
        record.status = status_var.get()
        record.llm_backend = llm_backend_var.get()
        record.llm_model = llm_model_var.get()
        return True

class JsonFormatter(logging.Formatter):
    """Formateur JSON simple pour les logs structurés."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: dict[str, Any] = {
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "run_id": getattr(record, "run_id", None),
            "node_id": getattr(record, "node_id", None),
            "request_id": getattr(record, "request_id", None),
            "status": getattr(record, "status", None),
            "llm_backend": getattr(record, "llm_backend", None),
            "llm_model": getattr(record, "llm_model", None),
            "message": record.getMessage(),
        }
        # Ajout de champs supplémentaires éventuels
        for key in ("method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)

def configure_logging() -> None:
    """Configure le root logger pour utiliser le formateur JSON."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

# Configure les logs dès l'import
configure_logging()
