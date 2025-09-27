"""add plan_versions table for plan snapshots

Revision ID: d1e2f3a4b5c6
Revises: c7a5b1d9cafe
Create Date: 2025-09-24 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "d1f2e3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": name}).scalar()
    return bool(row)


def _has_column(conn, table: str, column: str) -> bool:
    row = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
            """
        ),
        {"t": table, "c": column},
    ).first()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()
    # Crée plan_versions si absent
    if not _table_exists(conn, "plan_versions"):
        op.create_table(
            "plan_versions",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("plan_id", pg.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
            sa.Column("numero_version", sa.Integer(), nullable=False),
            sa.Column("graph", pg.JSONB(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_plan_versions_plan ON plan_versions(plan_id)")
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_versions_unique ON plan_versions(plan_id, numero_version)"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "plan_versions"):
        op.drop_index("uq_plan_versions_unique", table_name="plan_versions")
        op.drop_index("ix_plan_versions_plan", table_name="plan_versions")
        op.drop_table("plan_versions")
