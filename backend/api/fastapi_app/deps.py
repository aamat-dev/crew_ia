from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import AsyncGenerator, Sequence

from fastapi import Header, HTTPException, status, Request, Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from zoneinfo import ZoneInfo
from datetime import timezone, datetime, timedelta

from core.telemetry.metrics import metrics_enabled, get_db_pool_in_use

logger = logging.getLogger(__name__)
_db_pool_hooks_attached = False

# Limite d'intervalle temporel (31 jours)
MAX_DATE_RANGE_DAYS = 31


def cap_date_range(
    start: datetime | None,
    end: datetime | None,
    max_days: int = MAX_DATE_RANGE_DAYS,
) -> None:
    """Vérifie que l'intervalle [start, end] ne dépasse pas ``max_days`` jours."""
    if start and end:
        if end < start:
            raise HTTPException(status_code=400, detail="bornes temporelles incohérentes")
        if end - start > timedelta(days=max_days):
            raise HTTPException(
                status_code=400,
                detail=f"intervalle limité à {max_days} jours",
            )


def _setup_db_pool_metrics(engine: AsyncEngine) -> None:
    global _db_pool_hooks_attached
    if _db_pool_hooks_attached or not metrics_enabled():
        return

    pool = getattr(getattr(engine, "sync_engine", engine), "pool", None)
    if pool is None:
        logger.debug("db_pool_in_use: aucun pool disponible, instrumentation ignorée")
        return

    def _checkout(*_, **__):
        if metrics_enabled():
            get_db_pool_in_use().labels(db="primary").inc()

    def _checkin(*_, **__):
        if metrics_enabled():
            get_db_pool_in_use().labels(db="primary").dec()

    try:
        event.listen(pool, "checkout", _checkout)
        event.listen(pool, "checkin", _checkin)
        _db_pool_hooks_attached = True
        logger.debug("db_pool_in_use hooks attached")
    except Exception:
        logger.debug("db_pool_in_use: échec de l'attachement des hooks", exc_info=True)


ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    # Provide sensible defaults so the API can start without mandatory
    # environment variables. Tests override the database connection so a
    # lightweight SQLite URL is sufficient here and a fixed API key keeps
    # the authentication logic enabled.
    database_url: str = Field(
        default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL"
    )
    api_key: str = Field(default="test-key", alias="API_KEY")
    allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="ALLOWED_ORIGINS",
    )
    artifacts_dir: str = Field(default=".runs", alias="ARTIFACTS_DIR")  # ← ajouté

    @property
    def allowed_origins(self) -> Sequence[str]:
        raw = self.allowed_origins_raw or ""
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# SQLAlchemy async engine/session (lecture seule côté API)
engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
_setup_db_pool_metrics(engine)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return SessionLocal


# Backwards compatibility: the tests expect a ``get_db`` dependency
# providing a database session.
get_db = get_session


def _check_api_key(x_api_key: str | None) -> bool:
    if settings.api_key and x_api_key == settings.api_key:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def api_key_auth(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> bool:
    """Ancienne dépendance conservée pour compatibilité tests."""
    return _check_api_key(x_api_key)


# -------- RBAC minimal ----------------------------------------------------
FEATURE_RBAC = os.getenv("FEATURE_RBAC", "false").lower() == "true"


async def read_role(
    request: Request, x_role: str | None = Header(default=None, alias="X-Role")
) -> str:
    """Lit le rôle depuis ``X-Role`` et le stocke dans ``request.state``.

    Si ``FEATURE_RBAC`` est activé, l'en-tête est obligatoire et doit valoir
    ``viewer``, ``editor`` ou ``admin``.
    """
    if not FEATURE_RBAC:
        role = x_role or "viewer"
        request.state.role = role
        return role

    allowed = {"viewer", "editor", "admin"}
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        role = x_role or "viewer"
        if x_role and x_role not in allowed:
            raise HTTPException(status_code=403, detail="RBAC: rôle requis")
        request.state.role = role
        return role

    if x_role not in allowed:
        raise HTTPException(status_code=403, detail="RBAC: rôle requis")
    request.state.role = x_role
    return x_role


def require_role(*allowed: str):
    """Dépendance vérifiant que ``role`` fait partie de ``allowed``."""

    async def _checker(role: str = Depends(read_role)) -> None:
        if FEATURE_RBAC and allowed and role not in allowed:
            raise HTTPException(status_code=403, detail="RBAC: accès refusé")

    return _checker

# X-Request-ID requis pour les mutations (brief)
async def require_request_id(x_request_id: str | None = Header(default=None, alias="X-Request-ID")) -> str:
    if not x_request_id:
        raise HTTPException(status_code=400, detail="X-Request-ID header is required")
    return x_request_id


# --- Auth API key ---------------------------------------------------------------
def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> bool:
    """
    Vérifie la clé API.
    - Les requêtes OPTIONS (preflight CORS) sont toujours autorisées.
    - L'endpoint /health est accessible sans authentification.
    """
    # Autoriser preflight CORS
    if request.method == "OPTIONS":
        return True
    # Exempter /health
    if request.url.path == "/health":
        return True
    return _check_api_key(x_api_key)


# Compatibilité ascendante
strict_api_key_auth = require_api_key


# Timezone optionnelle pour formatage
async def read_timezone(x_timezone: str | None = Header(default=None, alias="X-Timezone")) -> ZoneInfo | None:
    if not x_timezone:
        return None
    try:
        return ZoneInfo(x_timezone)
    except Exception:
        # On ignore une TZ invalide : la réponse reste en UTC
        return None


# Helpers temps
def to_tz(dt: datetime | None, tz: ZoneInfo | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz) if tz else dt.astimezone(timezone.utc)
