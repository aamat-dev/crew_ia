from __future__ import annotations

import uuid
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.log import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Propager X-Request-ID, l’attacher au state et logger l’accès (api.access)."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api.access")

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = rid
        token = request_id_var.set(rid)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        self.logger.info(
            "access",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response
