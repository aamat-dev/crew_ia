from __future__ import annotations

import time
from typing import Any

from ..observability.metrics import (
    metrics_enabled,
    get_http_requests_total,
    get_http_requests_total_family,
    get_http_request_duration_seconds,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any):  # type: ignore[override]
        if not metrics_enabled():
            return await call_next(request)

        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start

            route_path = "/unknown"
            route = request.scope.get("route")
            if route is not None:
                route_path = getattr(route, "path", None) or getattr(route, "path_format", "/unknown")
            method = request.method
            status = str(status_code)
            status_family = f"{status_code // 100}xx"

            get_http_requests_total().labels(route_path, method, status).inc()
            get_http_requests_total_family().labels(route_path, method, status_family).inc()
            get_http_request_duration_seconds().labels(route_path, method).observe(duration)

        return response
