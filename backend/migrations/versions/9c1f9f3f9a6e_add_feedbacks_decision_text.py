"""add decision_text generated column on feedbacks

Revision ID: 9c1f9f3f9a6e
Revises: 40c0f6d462ff
Create Date: 2025-09-08 20:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9c1f9f3f9a6e"
down_revision: Union[str, Sequence[str], None] = "40c0f6d462ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajoute une colonne générée decision_text (extrait evaluation->>'decision')
    # Postgres 12+: STORED generated column
    conn = op.get_bind()
    # Vérifie l'existence de la colonne
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'feedbacks' AND column_name = 'decision_text'
            """
        )
    ).first()
    if not exists:
        op.execute(
            "ALTER TABLE feedbacks ADD COLUMN decision_text TEXT GENERATED ALWAYS AS ((evaluation->>'decision')) STORED"
        )
    # Index pour requêtes d'agrégat
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_feedbacks_run_decision ON feedbacks(run_id, decision_text)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_feedbacks_run_decision")
    # On ne peut pas utiliser op.drop_column facilement pour une colonne générée avec certaines versions,
    # on passe par SQL direct.
    op.execute("ALTER TABLE feedbacks DROP COLUMN IF EXISTS decision_text")

