# backend/migrations/env.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# --- Alembic config ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Assure que Python voit le projet ---
# env.py est dans backend/migrations → parents[2] = racine du repo
ROOT = Path(__file__).resolve().parents[2]
# On ajoute le repo root (pour importer "backend.*") et "backend/" (pour importer "core.*")
for p in (ROOT, ROOT / "backend"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

# --- Importe les modèles pour peupler SQLModel.metadata ---
# (toute la DDL vient d'ici)
from core.storage import db_models as _  # noqa: F401

# --- Cible des migrations ---
target_metadata = SQLModel.metadata

def _sync_url() -> str:
    """
    Récupère l'URL DB synchrone pour Alembic (priorité env).
    1) ALEMBIC_DATABASE_URL
    2) DATABASE_URL_SYNC
    3) DATABASE_URL converti (asyncpg -> psycopg)
    """
    env_alembic = os.getenv("ALEMBIC_DATABASE_URL")
    if env_alembic:
        return env_alembic

    env_sync = os.getenv("DATABASE_URL_SYNC")
    if env_sync:
        return env_sync

    env = os.getenv("DATABASE_URL")
    if env:
        if env.startswith("postgresql+asyncpg"):
            return env.replace("postgresql+asyncpg", "postgresql+psycopg", 1)
        return env

    # fallback éventuel: valeur dans alembic.ini
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    raise RuntimeError(
        "Aucune URL de BDD trouvée. Définis ALEMBIC_DATABASE_URL ou DATABASE_URL(_SYNC)."
    )

def run_migrations_offline() -> None:
    url = _sync_url()
    config.set_main_option("sqlalchemy.url", url)
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
    config.set_main_option("sqlalchemy.url", url)
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
