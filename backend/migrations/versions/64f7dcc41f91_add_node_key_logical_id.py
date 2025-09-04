"""add node.key (logical id)"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "64f7dcc41f91"
down_revision = "91570da90011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("nodes", sa.Column("key", sa.String(), nullable=True))
    op.create_index("ix_nodes_key", "nodes", ["key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_nodes_key", table_name="nodes")
    op.drop_column("nodes", "key")
