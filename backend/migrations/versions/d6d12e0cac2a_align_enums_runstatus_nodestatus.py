from alembic import op

# Utilise l'ID réel du fichier (recommandé)
revision = "d6d12e0cac2a"
down_revision = "855034941b26"
branch_labels = None
depends_on = None

def upgrade():
    # RUNSTATUS
    op.execute("""
    DO $do$
    BEGIN
      -- rename legacy 'success' -> 'completed' if present
      IF EXISTS (
        SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'runstatus' AND e.enumlabel = 'success'
      ) THEN
        ALTER TYPE runstatus RENAME VALUE 'success' TO 'completed';
      END IF;

      -- ensure 'completed'
      IF NOT EXISTS (
        SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'runstatus' AND e.enumlabel = 'completed'
      ) THEN
        ALTER TYPE runstatus ADD VALUE 'completed';
      END IF;

      -- ensure 'failed'
      IF NOT EXISTS (
        SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'runstatus' AND e.enumlabel = 'failed'
      ) THEN
        ALTER TYPE runstatus ADD VALUE 'failed';
      END IF;
    END
    $do$;
    """)

    # NODESTATUS
    op.execute("""
    DO $do$
    BEGIN
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
    $do$;
    """)

def downgrade():
    # Pas de downgrade sûr pour les ENUM -> no-op
    pass
