# alembic/env.py
from __future__ import annotations
import os

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# --- Importe tes modèles pour que SQLModel.metadata soit peuplé ---
# Modèles existants
from core.storage.db_models import Run, Node, Artifact, Event  # noqa: F401
# Modèles de l'application
from app.db.base import Base  # noqa: F401
from dotenv import load_dotenv
load_dotenv()  # charge le .env tôt

# Si tu veux forcer alembic à lire l'URL depuis l'env:
db_url = os.getenv("ALEMBIC_DATABASE_URL")
if db_url:
    context.config.set_main_option("sqlalchemy.url", db_url)

# Alembic Config object
config = context.config

# Cible des migrations
target_metadata = SQLModel.metadata

def _sync_url() -> str:
    """
    Récupère l'URL de BDD pour Alembic (driver *synchrone*).

    Priorité :
      1) ALEMBIC_DATABASE_URL (si défini)
      2) DATABASE_URL_SYNC (si défini)
      3) DATABASE_URL converti (remplace 'postgresql+asyncpg' -> 'postgresql+psycopg')
    """
    env_alembic = os.getenv("ALEMBIC_DATABASE_URL")
    if env_alembic:
        return env_alembic

    env_sync = os.getenv("DATABASE_URL_SYNC")
    if env_sync:
        return env_sync

    env = os.getenv("DATABASE_URL")
    if env:
        # SQLAlchemy 2.x : driver sync moderne = 'postgresql+psycopg'
        if env.startswith("postgresql+asyncpg"):
            return env.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
        return env

    raise RuntimeError(
        "Aucune URL de BDD trouvée. Définis ALEMBIC_DATABASE_URL, DATABASE_URL ou DATABASE_URL_SYNC (dans .env).",
    )

def run_migrations_offline() -> None:
    url = _sync_url()
    config.set_main_option("sqlalchemy.url", url)  # <—
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    url = _sync_url()
    config.set_main_option("sqlalchemy.url", url)  # <—
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
