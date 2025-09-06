from alembic import op
import sqlalchemy as sa

revision = "20240907_node_key_not_null"
down_revision = "20240905_nodes_run_key_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE nodes SET key = id::text WHERE key IS NULL")
    op.alter_column("nodes", "key", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    op.alter_column("nodes", "key", existing_type=sa.String(), nullable=True)
