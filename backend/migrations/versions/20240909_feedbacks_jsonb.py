"""convert feedbacks metadata/evaluation to jsonb"""

from alembic import op

revision = "20240909_feedbacks_jsonb"
down_revision = "20240908_jsonb_meta_nodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE feedbacks ALTER COLUMN metadata  TYPE jsonb USING metadata::jsonb;"
    )
    op.execute(
        "ALTER TABLE feedbacks ALTER COLUMN evaluation TYPE jsonb USING evaluation::jsonb;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE feedbacks ALTER COLUMN metadata  TYPE json  USING metadata::json;"
    )
    op.execute(
        "ALTER TABLE feedbacks ALTER COLUMN evaluation TYPE json  USING evaluation::json;"
    )

