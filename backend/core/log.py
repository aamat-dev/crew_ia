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
    """Formateur JSON pour logs structurés avec stacktrace.

    Expose à la fois des clés explicites (timestamp, level, logger, message)
    et des alias demandés (ts, module, msg, stacktrace) pour compatibilité.
    """

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        # Base
        ts = dt.datetime.utcnow().isoformat() + "Z"
        msg = record.getMessage()
        # Déduit le service à partir du logger
        service = None
        name = record.name or ""
        if name.startswith("api.") or name == "api.access":
            service = "api"
        elif name.startswith("orchestrator."):
            service = "orchestrator"

        payload: dict[str, Any] = {
            # Clés historiques
            "timestamp": ts,
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": msg,
            # Alias demandés
            "ts": ts,
            "module": record.name,
            "msg": msg,
            "service": service,
            # Contexte
            "request_id": getattr(record, "request_id", None),
            "run_id": getattr(record, "run_id", None),
            "node_id": getattr(record, "node_id", None),
            "status": getattr(record, "status", None),
            "llm_backend": getattr(record, "llm_backend", None),
            "llm_model": getattr(record, "llm_model", None),
        }
        # Alias trace_id pour compat outillage
        if payload.get("request_id"):
            payload["trace_id"] = payload["request_id"]
        # Champs additionnels éventuels (ex: middleware d'accès)
        for key in ("method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        # Stacktrace si présent
        if record.exc_info:
            try:
                payload["stacktrace"] = self.formatException(record.exc_info)
            except Exception:
                payload["stacktrace"] = "<unavailable>"
        return json.dumps(payload, ensure_ascii=False)

def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

# Configure au chargement du module
configure_logging()
