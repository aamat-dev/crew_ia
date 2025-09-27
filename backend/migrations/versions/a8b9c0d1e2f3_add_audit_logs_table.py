"""add audit_logs table for operator journaling

Revision ID: a8b9c0d1e2f3
Revises: f0a1b2c3d4e5
Create Date: 2025-10-05 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": name}).scalar()
    return bool(row)


def _enum_exists(conn, name: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :n)"
        ),
        {"n": name},
    ).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()
    if not _enum_exists(conn, "auditsource"):
        conn.execute(sa.text("CREATE TYPE auditsource AS ENUM ('system', 'human')"))
    auditsource_for_column = pg.ENUM(
        "system",
        "human",
        name="auditsource",
        create_type=False,
    )

    if not _table_exists(conn, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("run_id", pg.UUID(as_uuid=True), nullable=True),
            sa.Column("node_id", pg.UUID(as_uuid=True), nullable=True),
            sa.Column("source", auditsource_for_column, nullable=False, server_default="human"),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("actor_role", sa.String(), nullable=True),
            sa.Column("actor", sa.String(), nullable=True),
            sa.Column("request_id", sa.String(), nullable=True),
            sa.Column("metadata", pg.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_audit_logs_run", "audit_logs", ["run_id"], unique=False)
        op.create_index("ix_audit_logs_node", "audit_logs", ["node_id"], unique=False)
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
        op.create_index("ix_audit_logs_actor_role", "audit_logs", ["actor_role"], unique=False)
        op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"], unique=False)
        op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False)
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "audit_logs"):
        op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
        op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
        op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
        op.drop_index("ix_audit_logs_actor_role", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_index("ix_audit_logs_node", table_name="audit_logs")
        op.drop_index("ix_audit_logs_run", table_name="audit_logs")
        op.drop_table("audit_logs")
    conn.execute(sa.text("DROP TYPE IF EXISTS auditsource"))
