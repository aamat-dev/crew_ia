"""convert feedbacks metadata/evaluation to jsonb"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20240909_feedbacks_jsonb"
down_revision = "20240908_jsonb_meta_nodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "feedbacks",
        "metadata",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(),
        postgresql_using="metadata::jsonb",
    )
    op.alter_column(
        "feedbacks",
        "evaluation",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(),
        postgresql_using="evaluation::jsonb",
    )


def downgrade() -> None:
    op.alter_column(
        "feedbacks",
        "metadata",
        existing_type=postgresql.JSONB(),
        type_=sa.JSON(),
        postgresql_using="metadata::json",
    )
    op.alter_column(
        "feedbacks",
        "evaluation",
        existing_type=postgresql.JSONB(),
        type_=sa.JSON(),
        postgresql_using="evaluation::json",
    )
