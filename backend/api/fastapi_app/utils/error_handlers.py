from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import AppError


def _http_code_to_app_code(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
        502: "bad_gateway",
        503: "unavailable",
        504: "timeout",
    }
    return mapping.get(int(status_code), "error")


def _make_body(detail: Any, code: str, hint: str | None = None) -> Dict[str, Any]:
    return {"detail": detail, "code": code, "hint": hint}


def setup_error_handlers(app: FastAPI) -> None:
    log = logging.getLogger("api.error")

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):  # type: ignore[override]
        # Log avec stacktrace et contexte request_id
        rid = getattr(request.state, "request_id", None)
        log.exception("app_error: %s", exc, extra={"request_id": rid})
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):  # type: ignore[override]
        rid = getattr(request.state, "request_id", None)
        # 5xx seulement: évite le bruit et tout coût inutile sur les 4xx attendues
        if exc.status_code >= 500:
            log.error("http_exception %s", exc.detail, extra={"request_id": rid})
        code = _http_code_to_app_code(exc.status_code)
        # Normalise detail (texte, dict, liste) sans l’altérer
        return JSONResponse(status_code=exc.status_code, content=_make_body(exc.detail, code))

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(request: Request, exc: RequestValidationError):  # type: ignore[override]
        rid = getattr(request.state, "request_id", None)
        log.warning("request_validation_error", extra={"request_id": rid})
        return JSONResponse(status_code=422, content=_make_body(exc.errors(), "validation_error"))
