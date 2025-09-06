from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "83c6c56308fb"
down_revision = "15d1c1466f53"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return conn.execute(text("SELECT to_regclass(:n)"), {"n": name}).scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # enlarge alembic_version.version_num to allow long revision identifiers
    op.execute(
        "ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"
    )

    # align enums runstatus / nodestatus
    op.execute(
        """
        DO $$
        BEGIN
          -- runstatus
          IF EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'runstatus' AND e.enumlabel = 'success'
          ) THEN
            ALTER TYPE runstatus RENAME VALUE 'success' TO 'completed';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'runstatus' AND e.enumlabel = 'completed'
          ) THEN
            ALTER TYPE runstatus ADD VALUE 'completed';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'runstatus' AND e.enumlabel = 'failed'
          ) THEN
            ALTER TYPE runstatus ADD VALUE 'failed';
          END IF;

          -- nodestatus
          IF EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'nodestatus' AND e.enumlabel = 'success'
          ) THEN
            ALTER TYPE nodestatus RENAME VALUE 'success' TO 'completed';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'nodestatus' AND e.enumlabel = 'completed'
          ) THEN
            ALTER TYPE nodestatus ADD VALUE 'completed';
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'nodestatus' AND e.enumlabel = 'failed'
          ) THEN
            ALTER TYPE nodestatus ADD VALUE 'failed';
          END IF;
        END
        $$;
        """
    )

    # nodes table
    if _table_exists(conn, "nodes"):
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS role VARCHAR")
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
        op.execute(
            "UPDATE nodes SET created_at=COALESCE(created_at, now()), updated_at=COALESCE(updated_at, now())"
        )

    # events table
    if _table_exists(conn, "events"):
        op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS request_id VARCHAR")
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_events_request_id ON events(request_id)"
        )

    # feedbacks table
    if _table_exists(conn, "feedbacks"):
        op.execute("ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS metadata JSONB")
        op.execute("ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS evaluation JSONB")

    # artifacts table
    if _table_exists(conn, "artifacts"):
        op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
        op.execute(
            "UPDATE artifacts SET created_at=COALESCE(created_at, now())"
        )

    # optional project tables
    optional = [
        "plans",
        "plan_tasks",
        "plan_assignments",
        "plan_reviews",
        "agents",
        "agent_models_matrix",
    ]
    for tbl in optional:
        if _table_exists(conn, tbl):
            op.execute(
                f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ"
            )
            op.execute(
                f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ"
            )
            op.execute(
                f"UPDATE {tbl} SET created_at=COALESCE(created_at, now()), updated_at=COALESCE(updated_at, now())"
            )


def downgrade() -> None:
    # aucun downgrade sûr
    pass
