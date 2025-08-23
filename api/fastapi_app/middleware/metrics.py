from __future__ import annotations

import time
from typing import Any

from core.telemetry.metrics import (
    metrics_enabled,
    get_http_requests_total,
    get_http_request_duration_seconds,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any):  # type: ignore[override]
        if not metrics_enabled():
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        route_path = "/unknown"
        route = request.scope.get("route")
        if route is not None:
            route_path = getattr(route, "path", None) or getattr(route, "path_format", "/unknown")
        method = request.method
        status = str(response.status_code)

        counter_labels = (route_path, method, status)
        hist_labels = (route_path, method)

        get_http_requests_total().labels(*counter_labels).inc()
        get_http_request_duration_seconds().labels(*hist_labels).observe(duration)

        return response
