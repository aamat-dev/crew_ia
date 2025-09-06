# backend/migrations/versions/83c6c56308fb_global_min_schema_patch.py
from __future__ import annotations

from alembic import op
from sqlalchemy import text

# --- Révisions Alembic ---
revision = "83c6c56308fb"
# ⚠️ Mets ici la VRAIE révision précédente de ton repo.
# D'après tes logs, c'était : 20240906_sanity_patch_min_schema
down_revision = "20240906_sanity_patch_min_schema"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT to_regclass(:tname) IS NOT NULL"),
            {"tname": name},
        ).scalar()
    )


def upgrade() -> None:
    conn = op.get_bind()

    # 0) Autoriser des identifiants de révision > 32 chars
    op.execute("ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")

    # 1) Harmoniser ENUMs runstatus/nodestatus (success -> completed ; ajouter completed/failed si manquants)
    op.execute(
        """
        DO $do$
        BEGIN
          -- RUNSTATUS
          IF EXISTS (SELECT 1 FROM pg_type WHERE typname='runstatus') THEN
            IF EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='runstatus' AND e.enumlabel='success'
            ) THEN
              ALTER TYPE runstatus RENAME VALUE 'success' TO 'completed';
            END IF;

            IF NOT EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='runstatus' AND e.enumlabel='completed'
            ) THEN
              ALTER TYPE runstatus ADD VALUE 'completed';
            END IF;

            IF NOT EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='runstatus' AND e.enumlabel='failed'
            ) THEN
              ALTER TYPE runstatus ADD VALUE 'failed';
            END IF;
          END IF;

          -- NODESTATUS
          IF EXISTS (SELECT 1 FROM pg_type WHERE typname='nodestatus') THEN
            IF EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='nodestatus' AND e.enumlabel='success'
            ) THEN
              ALTER TYPE nodestatus RENAME VALUE 'success' TO 'completed';
            END IF;

            IF NOT EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='nodestatus' AND e.enumlabel='completed'
            ) THEN
              ALTER TYPE nodestatus ADD VALUE 'completed';
            END IF;

            IF NOT EXISTS (
              SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
              WHERE t.typname='nodestatus' AND e.enumlabel='failed'
            ) THEN
              ALTER TYPE nodestatus ADD VALUE 'failed';
            END IF;
          END IF;
        END
        $do$;
        """
    )

    # 2) nodes: role, created_at, updated_at
    if _table_exists(conn, "nodes"):
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS role VARCHAR")
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
        op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
        op.execute(
            "UPDATE nodes SET created_at=COALESCE(created_at, now()), updated_at=COALESCE(updated_at, now())"
        )

    # 3) events: request_id (+ index)
    if _table_exists(conn, "events"):
        op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS request_id VARCHAR")
        op.execute("CREATE INDEX IF NOT EXISTS ix_events_request_id ON events(request_id)")

    # 4) feedbacks: JSONB metadata/evaluation
    if _table_exists(conn, "feedbacks"):
        op.execute("ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS metadata JSONB")
        op.execute("ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS evaluation JSONB")

    # 5) artifacts: created_at
    if _table_exists(conn, "artifacts"):
        op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
        op.execute("UPDATE artifacts SET created_at=COALESCE(created_at, now())")

    # 6) Tables optionnelles du projet : timestamps si présentes
    for tbl in ["plans", "plan_tasks", "plan_assignments", "plan_reviews", "agents", "agent_models_matrix"]:
        if _table_exists(conn, tbl):
            op.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
            op.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")
            op.execute(
                f"UPDATE {tbl} SET created_at=COALESCE(created_at, now()), updated_at=COALESCE(updated_at, now())"
            )


def downgrade() -> None:
    # Aucun downgrade sûr (no-op)
    pass
