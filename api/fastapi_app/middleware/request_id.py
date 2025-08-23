from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

import sentry_sdk


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and log access in JSON format."""

    def __init__(self, app):
        super().__init__(app)
        # Dedicated logger so uvicorn's access formatter is untouched
        self.logger = logging.getLogger("api.access")

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        sentry_sdk.set_tag("request_id", rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            sentry_sdk.capture_exception()
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        self.logger.info(
            json.dumps(
                {
                    "request_id": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )
        return response
