"""convert metadata and deps to jsonb"""

from alembic import op

revision = "20240908_jsonb_meta_nodes"
down_revision = "20240907_node_key_not_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE runs  ALTER COLUMN metadata TYPE jsonb USING metadata::jsonb;")
    op.execute("ALTER TABLE nodes ALTER COLUMN deps      TYPE jsonb USING deps::jsonb;")


def downgrade() -> None:
    op.execute("ALTER TABLE runs  ALTER COLUMN metadata TYPE json  USING metadata::json;")
    op.execute("ALTER TABLE nodes ALTER COLUMN deps      TYPE json  USING deps::json;")
