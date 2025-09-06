"""sanity.patch.min.schema

Revision ID: 15d1c1466f53
Revises: 6518822eb171_add_events_request_id
Create Date: 2025-09-06 14:12:05.539486

"""
from alembic import op

revision = "20240906_sanity_patch_min_schema"
down_revision = "6518822eb171"
branch_labels = None
depends_on = None

def upgrade():
    # EVENTS
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS request_id VARCHAR")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_request_id ON events(request_id)")

    # NODES
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS role VARCHAR")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")

    # ENUMS (sécurité, idempotent)
    op.execute("""
    DO $do$
    BEGIN
      -- runstatus
      IF EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                 WHERE t.typname='runstatus' AND e.enumlabel='success') THEN
        ALTER TYPE runstatus RENAME VALUE 'success' TO 'completed';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                     WHERE t.typname='runstatus' AND e.enumlabel='completed') THEN
        ALTER TYPE runstatus ADD VALUE 'completed';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                     WHERE t.typname='runstatus' AND e.enumlabel='failed') THEN
        ALTER TYPE runstatus ADD VALUE 'failed';
      END IF;

      -- nodestatus
      IF EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                 WHERE t.typname='nodestatus' AND e.enumlabel='success') THEN
        ALTER TYPE nodestatus RENAME VALUE 'success' TO 'completed';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                     WHERE t.typname='nodestatus' AND e.enumlabel='completed') THEN
        ALTER TYPE nodestatus ADD VALUE 'completed';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
                     WHERE t.typname='nodestatus' AND e.enumlabel='failed') THEN
        ALTER TYPE nodestatus ADD VALUE 'failed';
      END IF;
    END
    $do$;
    """)

    # Contrainte d’unicité nodes(run_id, key) – safe add
    op.execute("""
    DO $do$
    BEGIN
      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname='nodes' AND c.conname='uq_nodes_run_id_key'
      ) THEN
        ALTER TABLE nodes ADD CONSTRAINT uq_nodes_run_id_key UNIQUE (run_id, key);
      END IF;
    END
    $do$;
    """)

def downgrade():
    # On laisse no-op pour rester simple et sûr
    pass
