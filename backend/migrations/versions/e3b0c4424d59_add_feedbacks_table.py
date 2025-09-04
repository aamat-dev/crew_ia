"""add feedbacks table"""

from alembic import op
import sqlalchemy as sa

revision = "e3b0c4424d59"
down_revision = "64f7dcc41f91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", sa.Uuid(), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_feedbacks_run_node_created_at", "feedbacks", ["run_id", "node_id", "created_at"])
    op.create_index("ix_feedbacks_run_id", "feedbacks", ["run_id"])
    op.create_index("ix_feedbacks_node_id", "feedbacks", ["node_id"])


def downgrade() -> None:
    op.drop_index("ix_feedbacks_run_node_created_at", table_name="feedbacks")
    op.drop_index("ix_feedbacks_run_id", table_name="feedbacks")
    op.drop_index("ix_feedbacks_node_id", table_name="feedbacks")
    op.drop_table("feedbacks")
