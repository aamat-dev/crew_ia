"""convert metadata and deps to jsonb"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20240908_jsonb_meta_nodes"
down_revision = "3998bc48da90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "runs",
        "metadata",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(),
        postgresql_using="metadata::jsonb",
    )
    op.alter_column(
        "nodes",
        "deps",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(),
        postgresql_using="deps::jsonb",
    )


def downgrade() -> None:
    op.alter_column(
        "runs",
        "metadata",
        existing_type=postgresql.JSONB(),
        type_=sa.JSON(),
        postgresql_using="metadata::json",
    )
    op.alter_column(
        "nodes",
        "deps",
        existing_type=postgresql.JSONB(),
        type_=sa.JSON(),
        postgresql_using="deps::json",
    )
