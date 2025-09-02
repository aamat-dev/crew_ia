"""add feedbacks.evaluation JSON

Revision ID: 20250902_01
Revises: 20250901_01_init_agents
Create Date: 2025-09-02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250902_01"
down_revision = "20250901_01_init_agents"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "feedbacks",
        sa.Column("evaluation", sa.JSON(), nullable=True),
    )

def downgrade():
    op.drop_column("feedbacks", "evaluation")
