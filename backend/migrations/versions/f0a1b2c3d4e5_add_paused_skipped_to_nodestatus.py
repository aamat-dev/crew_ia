"""
Add 'paused' and 'skipped' to nodestatus ENUM (PostgreSQL).

Revision ID: f0a1b2c3d4e5
Revises: e2a3b4c5d6f7_add_tasks_archived_column
Create Date: 2025-09-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f0a1b2c3d4e5"
down_revision = "e2a3b4c5d6f7"
branch_labels = None
depends_on = None


def _is_postgres(conn) -> bool:
    try:
        name = conn.dialect.name
        return name == "postgresql"
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        # No-op for non-PostgreSQL backends
        return

    # Safe add value if not exists — compatible with older PG versions
    op.execute(
        """
        DO $$ BEGIN
            BEGIN
                ALTER TYPE nodestatus ADD VALUE 'paused';
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END;
            BEGIN
                ALTER TYPE nodestatus ADD VALUE 'skipped';
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END;
        END $$;
        """
    )


def downgrade() -> None:
    # Removing ENUM values in PostgreSQL is non-trivial and unsafe; no-op
    pass
