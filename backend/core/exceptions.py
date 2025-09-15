from __future__ import annotations

from typing import Any, Optional, Dict


class AppError(Exception):
    """Base pour les erreurs métier applicatives.

    Porte un code stable, un status HTTP suggéré et un hint optionnel.
    """

    code: str = "app_error"
    http_status: int = 500

    def __init__(self, message: str, *, hint: Optional[str] = None, details: Any | None = None):
        super().__init__(message)
        self.hint = hint
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detail": str(self),
            "code": self.code,
            "hint": self.hint,
        }


class BadRequestError(AppError):
    code = "bad_request"
    http_status = 400


class PlanValidationError(BadRequestError):
    code = "plan_invalid"


class ResourceConflict(AppError):
    code = "conflict"
    http_status = 409


class NotFoundError(AppError):
    code = "not_found"
    http_status = 404


class UnauthorizedError(AppError):
    code = "unauthorized"
    http_status = 401


class ForbiddenError(AppError):
    code = "forbidden"
    http_status = 403


class RateLimitExceeded(AppError):
    code = "rate_limited"
    http_status = 429


class PersistenceError(AppError):
    code = "persistence_error"
    http_status = 500


class DependencyError(AppError):
    code = "dependency_error"
    http_status = 502


class OrchestratorFailure(AppError):
    code = "orchestrator_failure"
    http_status = 500


class ServiceTimeout(AppError):
    code = "timeout"
    http_status = 504

