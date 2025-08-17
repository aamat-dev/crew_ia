from __future__ import annotations
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from alembic.autogenerate import renderers
from sqlmodel.sql.sqltypes import AutoString
import sqlalchemy as sa
from sqlmodel import SQLModel
from core.storage.db_models import Run, Node, Artifact, Event  # noqa: F401

config = context.config

alembic_url = os.getenv("ALEMBIC_DATABASE_URL")
if alembic_url:
    config.set_main_option("sqlalchemy.url", alembic_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

@renderers.dispatch_for(AutoString)
def render_autostring(type_, autogen_context):
    return "sa.String()"