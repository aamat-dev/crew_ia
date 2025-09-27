"""add archived column on tasks

Revision ID: e2a3b4c5d6f7
Revises: d1e2f3a4b5c6
Create Date: 2025-09-24 00:30:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e2a3b4c5d6f7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'tasks' AND column_name = 'archived'
            """
        )
    ).first()
    if not exists:
        op.add_column("tasks", sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")))


def downgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'tasks' AND column_name = 'archived'
            """
        )
    ).first()
    if exists:
        op.drop_column("tasks", "archived")

