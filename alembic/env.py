# alembic/env.py
from __future__ import annotations
import os

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# --- Importe tes modèles pour que SQLModel.metadata soit peuplé ---
from core.storage.db_models import Run, Node, Artifact, Event  # noqa: F401

# Alembic Config object
config = context.config

# Cible des migrations
target_metadata = SQLModel.metadata

def _sync_url() -> str:
    """
    Récupère l'URL de BDD pour Alembic (driver *synchrone*).
    Priorité :
      1) DATABASE_URL_SYNC (si défini)
      2) DATABASE_URL converti (remplace 'postgresql+asyncpg' -> 'postgresql+psycopg2')
      3) valeur dans alembic.ini (sqlalchemy.url), si présente
    """
    env_sync = os.getenv("DATABASE_URL_SYNC")
    if env_sync:
        return env_sync

    env = os.getenv("DATABASE_URL")
    if env:
        if env.startswith("postgresql+asyncpg"):
            return env.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
        return env

    # fallback: alembic.ini
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        # si quelqu'un a mis l'async dans alembic.ini, convertissons aussi
        if ini_url.startswith("postgresql+asyncpg"):
            return ini_url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
        return ini_url

    raise RuntimeError(
        "Aucune URL de BDD trouvée. Définis DATABASE_URL ou DATABASE_URL_SYNC, "
        "ou mets sqlalchemy.url dans alembic.ini."
    )

def run_migrations_offline() -> None:
    url = _sync_url()
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
