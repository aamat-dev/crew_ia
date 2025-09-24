"""add indexes on agent_templates and agent_models_matrix

Revision ID: d1f2e3c4b5a6
Revises: c7a5b1d9cafe
Create Date: 2025-09-23 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1f2e3c4b5a6"
down_revision: Union[str, Sequence[str], None] = "c7a5b1d9cafe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(conn, index_name: str) -> bool:
    row = conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": index_name}).scalar()
    return bool(row)


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": table_name}).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()

    # agent_templates (role, domain, is_active, created_at)
    if _table_exists(conn, "agent_templates") and not _index_exists(
        conn, "public.ix_agent_templates_role_domain_active_created_at"
    ):
        op.create_index(
            "ix_agent_templates_role_domain_active_created_at",
            "agent_templates",
            ["role", "domain", "is_active", "created_at"],
            unique=False,
        )

    # agent_models_matrix (role, domain, is_active, created_at)
    if _table_exists(conn, "agent_models_matrix") and not _index_exists(
        conn, "public.ix_agent_models_matrix_role_domain_active_created_at"
    ):
        op.create_index(
            "ix_agent_models_matrix_role_domain_active_created_at",
            "agent_models_matrix",
            ["role", "domain", "is_active", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _index_exists(conn, "public.ix_agent_models_matrix_role_domain_active_created_at"):
        op.drop_index(
            "ix_agent_models_matrix_role_domain_active_created_at",
            table_name="agent_models_matrix",
        )
    if _index_exists(conn, "public.ix_agent_templates_role_domain_active_created_at"):
        op.drop_index(
            "ix_agent_templates_role_domain_active_created_at",
            table_name="agent_templates",
        )

