from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Any


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log chaque requête HTTP avec son statut."""
    # S'assure que le logger propage aux handlers globaux (capturé par caplog)
    logging.getLogger("api.access").propagate = True

    async def dispatch(self, request: Request, call_next: Any):  # type: ignore[override]
        # Log d'entrée avec le X-Request-ID si déjà présent
        rid = getattr(request.state, "request_id", None)
        logging.getLogger("api.access").info(
            "START %s %s",
            request.method,
            request.url.path,
            extra={"request_id": rid},
        )
        response = await call_next(request)
        rid = rid or response.headers.get("X-Request-ID")
        logging.getLogger("api.access").info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={"request_id": rid},
        )
        return response
