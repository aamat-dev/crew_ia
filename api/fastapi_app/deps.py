from __future__ import annotations
import os
from functools import lru_cache
from typing import AsyncGenerator, Sequence

from fastapi import Depends, Header, HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from zoneinfo import ZoneInfo
from datetime import timezone
from pydantic import Field

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
engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Backwards compatibility: the tests expect a ``get_db`` dependency
# providing a database session.
get_db = get_session

# Auth par clé API
async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

# Some test utilities look for a ``require_auth`` dependency. Provide an
# alias so it can be overridden easily during testing.
require_auth = require_api_key

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
from datetime import datetime

def to_tz(dt: datetime | None, tz: ZoneInfo | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz) if tz else dt.astimezone(timezone.utc)