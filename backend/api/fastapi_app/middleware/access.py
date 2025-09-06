from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Any


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log chaque requête HTTP avec son statut."""

    async def dispatch(self, request: Request, call_next: Any):  # type: ignore[override]
        response = await call_next(request)
        rid = getattr(request.state, "request_id", None) or response.headers.get("X-Request-ID")
        logging.getLogger("api.access").info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={"request_id": rid},
        )
        return response
