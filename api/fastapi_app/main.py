"""Entry point for FastAPI application.

This module exposes the FastAPI ``app`` instance so tests and
runners can import it using ``from api.fastapi_app.main import app``.
"""

from .app import app

__all__ = ["app"]
