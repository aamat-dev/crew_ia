"""add runs.metadata column if missing

Revision ID: ab12cd34ef56
Revises: 9c1f9f3f9a6e
Create Date: 2025-09-11 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "ab12cd34ef56"
down_revision: Union[str, Sequence[str], None] = "9c1f9f3f9a6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajoute la colonne JSONB "metadata" sur runs si absente (idempotent)
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'runs' AND column_name = 'metadata'
            """
        )
    ).first()
    if not exists:
        op.add_column("runs", sa.Column("metadata", pg.JSONB(), nullable=True))


def downgrade() -> None:
    # Suppression prudente (si présente)
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'runs' AND column_name = 'metadata'
            """
        )
    ).first()
    if exists:
        op.drop_column("runs", "metadata")

