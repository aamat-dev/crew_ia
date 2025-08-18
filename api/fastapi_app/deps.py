from __future__ import annotations
import os
from functools import lru_cache
from typing import AsyncGenerator, Sequence

from fastapi import Header, HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from zoneinfo import ZoneInfo
from datetime import timezone, datetime

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Provide sensible defaults so the API can start without mandatory
    # environment variables. Tests override the database connection so a
    # lightweight SQLite URL is sufficient here and a fixed API key keeps
    # the authentication logic enabled.
    database_url: str = Field(
        default="sqlite+aiosqlite:///./app.db", alias="DATABASE_URL"
    )
    api_key: str = Field(default="test-key", alias="API_KEY")
    cors_origins_raw: str = Field(default="", alias="CORS_ORIGINS")
    artifacts_dir: str = Field(default=".runs", alias="ARTIFACTS_DIR")  # ← ajouté

    @property
    def cors_origins(self) -> Sequence[str]:
        raw = self.cors_origins_raw or ""
        return [o.strip() for o in raw.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

# SQLAlchemy async engine/session (lecture seule côté API)
engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
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

# Auth par clé API
def api_key_auth(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if settings.api_key and x_api_key == settings.api_key:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )

# alias pour compatibilité
require_api_key = api_key_auth
require_auth = api_key_auth

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

