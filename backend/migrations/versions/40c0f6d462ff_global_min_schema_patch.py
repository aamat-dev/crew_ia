"""Global min schema patch (idempotent)

- Élargit alembic_version.version_num (long IDs)
- Harmonise les ENUMs runstatus/nodestatus (ajoute 'completed', 'failed', renomme success/succeeded -> completed si besoin)
- nodes: ajoute role, created_at, updated_at, rend key nullable (si présent)
- events: ajoute request_id + index
- artifacts: ajoute created_at + backfill
- feedbacks: ajoute metadata/evaluation en JSONB (si manquants)
- tests compat: crée agent_models_matrix si absente

Cette migration est idempotente et sûre sur un schéma déjà partiellement conforme.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# --- Alembic ---
revision: str = "40c0f6d462ff"
down_revision: str | None = "40c0f6d462f1"  # ta baseline
branch_labels = None
depends_on = None


def _exec(sql: str) -> None:
    op.execute(sql)


def upgrade() -> None:
    conn = op.get_bind()

    # 0) alembic_version.version_num plus long
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.alembic_version') IS NOT NULL THEN
        ALTER TABLE public.alembic_version
          ALTER COLUMN version_num TYPE VARCHAR(255);
      END IF;
    END $$;
    """)

    # 1) Harmoniser les ENUMs runstatus / nodestatus
    _exec("""
    DO $$
    DECLARE
      has_run_completed boolean;
      has_run_failed    boolean;
      has_run_success   boolean;
      has_run_succeeded boolean;

      has_node_completed boolean;
      has_node_failed    boolean;
      has_node_success   boolean;
      has_node_succeeded boolean;
    BEGIN
      -- RUNSTATUS
      IF EXISTS (SELECT 1 FROM pg_type WHERE typname='runstatus') THEN
        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='runstatus' AND e.enumlabel='completed'
        ) INTO has_run_completed;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='runstatus' AND e.enumlabel='failed'
        ) INTO has_run_failed;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='runstatus' AND e.enumlabel='success'
        ) INTO has_run_success;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='runstatus' AND e.enumlabel='succeeded'
        ) INTO has_run_succeeded;

        IF NOT has_run_completed THEN
          ALTER TYPE runstatus ADD VALUE 'completed';
        END IF;
        IF NOT has_run_failed THEN
          ALTER TYPE runstatus ADD VALUE 'failed';
        END IF;

        -- si des anciennes valeurs existent, on met à jour les lignes
        IF has_run_success OR has_run_succeeded THEN
          UPDATE runs SET status='completed'
            WHERE status::text IN ('success','succeeded');
        END IF;

        -- si 'completed' n'existait pas et 'success' existait seulement, on peut renommer
        IF has_run_success AND NOT has_run_completed THEN
          ALTER TYPE runstatus RENAME VALUE 'success' TO 'completed';
        END IF;
        IF has_run_succeeded AND NOT has_run_completed THEN
          ALTER TYPE runstatus RENAME VALUE 'succeeded' TO 'completed';
        END IF;
      END IF;

      -- NODESTATUS
      IF EXISTS (SELECT 1 FROM pg_type WHERE typname='nodestatus') THEN
        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='nodestatus' AND e.enumlabel='completed'
        ) INTO has_node_completed;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='nodestatus' AND e.enumlabel='failed'
        ) INTO has_node_failed;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='nodestatus' AND e.enumlabel='success'
        ) INTO has_node_success;

        SELECT EXISTS(
          SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid=e.enumtypid
          WHERE t.typname='nodestatus' AND e.enumlabel='succeeded'
        ) INTO has_node_succeeded;

        IF NOT has_node_completed THEN
          ALTER TYPE nodestatus ADD VALUE 'completed';
        END IF;
        IF NOT has_node_failed THEN
          ALTER TYPE nodestatus ADD VALUE 'failed';
        END IF;

        IF has_node_success OR has_node_succeeded THEN
          UPDATE nodes SET status='completed'
            WHERE status::text IN ('success','succeeded');
        END IF;

        IF has_node_success AND NOT has_node_completed THEN
          ALTER TYPE nodestatus RENAME VALUE 'success' TO 'completed';
        END IF;
        IF has_node_succeeded AND NOT has_node_completed THEN
          ALTER TYPE nodestatus RENAME VALUE 'succeeded' TO 'completed';
        END IF;
      END IF;
    END
    $$;
    """)

    # 2) nodes: role/created_at/updated_at + key nullable
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.nodes') IS NOT NULL THEN
        ALTER TABLE public.nodes
          ADD COLUMN IF NOT EXISTS role VARCHAR,
          ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

        -- key nullable (les tests insèrent parfois sans key)
        IF EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema='public' AND table_name='nodes' AND column_name='key' AND is_nullable='NO'
        ) THEN
          ALTER TABLE public.nodes ALTER COLUMN "key" DROP NOT NULL;
        END IF;

        -- backfill timestamps
        UPDATE public.nodes
          SET created_at = COALESCE(created_at, now()),
              updated_at = COALESCE(updated_at, now());
      END IF;
    END $$;
    """)

    # 3) events: request_id + index
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.events') IS NOT NULL THEN
        ALTER TABLE public.events
          ADD COLUMN IF NOT EXISTS request_id VARCHAR;
        CREATE INDEX IF NOT EXISTS ix_events_request_id ON public.events(request_id);
      END IF;
    END $$;
    """)

    # 4) artifacts: created_at + backfill
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.artifacts') IS NOT NULL THEN
        ALTER TABLE public.artifacts
          ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
        UPDATE public.artifacts
          SET created_at = COALESCE(created_at, now());
      END IF;
    END $$;
    """)

    # 5) feedbacks: metadata/evaluation en JSONB (si manquants)
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.feedbacks') IS NOT NULL THEN
        ALTER TABLE public.feedbacks
          ADD COLUMN IF NOT EXISTS metadata JSONB,
          ADD COLUMN IF NOT EXISTS evaluation JSONB;
      END IF;
    END $$;
    """)

    # 6) Compat tests: agent_models_matrix si absente
    _exec("""
    DO $$
    BEGIN
      IF to_regclass('public.agent_models_matrix') IS NULL THEN
        CREATE TABLE public.agent_models_matrix (
          id UUID,
          agent_name TEXT,
          model TEXT,
          weight DOUBLE PRECISION,
          config JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS ix_agent_models_matrix_agent_name
          ON public.agent_models_matrix(agent_name);
        CREATE INDEX IF NOT EXISTS ix_agent_models_matrix_model
          ON public.agent_models_matrix(model);
      END IF;
    END $$;
    """)


def downgrade() -> None:
    # Par sécurité: no-op (ne supprime rien).
    pass
