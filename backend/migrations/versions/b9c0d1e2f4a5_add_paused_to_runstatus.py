"""add paused to runstatus enum

Revision ID: b9c0d1e2f4a5
Revises: a8b9c0d1e2f3
Create Date: 2025-10-05 13:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b9c0d1e2f4a5"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def _is_postgres(conn) -> bool:
    try:
        return conn.dialect.name == "postgresql"
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        return
    op.execute(
        """
        DO $$ BEGIN
            BEGIN
                ALTER TYPE runstatus ADD VALUE 'paused';
            EXCEPTION
                WHEN duplicate_object THEN NULL;
            END;
        END $$;
        """
    )


def downgrade() -> None:
    # La suppression d'une valeur ENUM est destructive; on ne l'applique pas.
    pass
