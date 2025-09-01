from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.log import request_id_var

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and log access in JSON format."""

    def __init__(self, app):
        super().__init__(app)
        # Dedicated logger so uvicorn's access formatter is untouched
        self.logger = logging.getLogger("api.access")

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = rid
        token = request_id_var.set(rid)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        self.logger.info(
            "access",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        request_id_var.reset(token)
        return response
