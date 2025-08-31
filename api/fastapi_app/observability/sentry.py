"""Initialisation et middleware Sentry."""
from __future__ import annotations

import os

import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def init_sentry() -> bool:
    """Initialise Sentry à partir des variables d'environnement."""
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENV", "dev"),
        release=os.getenv("RELEASE", "crew_ia@dev"),
    )
    return True


class SentryContextMiddleware(BaseHTTPMiddleware):
    """Annote les événements Sentry avec contexte requête."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        rid = getattr(request.state, "request_id", None)
        if rid:
            sentry_sdk.set_tag("request_id", rid)
        try:
            response = await call_next(request)
        except Exception:
            sentry_sdk.set_tag("route", request.url.path)
            sentry_sdk.set_tag("status", 500)
            raise
        sentry_sdk.set_tag("route", request.url.path)
        sentry_sdk.set_tag("status", response.status_code)
        return response
