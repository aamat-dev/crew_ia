"""read-only perf indexes (idempotent + column guards)"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250818_indexes_readonly"
down_revision = "91570da90011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NB: on cible le schéma 'public' explicitement (Postgres par défaut)
    # Chaque bloc DO $$ ... $$ vérifie l'existence des colonnes avant CREATE INDEX.

    # events: filtre par run_id + tri timestamp desc
    op.execute(sa.text("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='events' AND column_name='timestamp'
      ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='events' AND column_name='run_id'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_events_run_ts_desc
          ON public.events (run_id, "timestamp" DESC);
      END IF;
    END $$;
    """))

    # artifacts: liste par node + tri created_at desc
    op.execute(sa.text("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='artifacts' AND column_name='created_at'
      ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='artifacts' AND column_name='node_id'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_artifacts_node_created_desc
          ON public.artifacts (node_id, created_at DESC);
      END IF;
    END $$;
    """))

    # nodes: par run + tri created_at desc, et clé logique
    op.execute(sa.text("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='nodes' AND column_name='created_at'
      ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='nodes' AND column_name='run_id'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_nodes_run_created_desc
          ON public.nodes (run_id, created_at DESC);
      END IF;

      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='nodes' AND column_name='key'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_nodes_key
          ON public.nodes ("key");
      END IF;
    END $$;
    """))

    # runs: tri par started_at desc, filtres courants
    op.execute(sa.text("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='runs' AND column_name='started_at'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_runs_started_desc
          ON public.runs (started_at DESC);
      END IF;

      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='runs' AND column_name='status'
      ) THEN
        CREATE INDEX IF NOT EXISTS ix_runs_status
          ON public.runs (status);
      END IF;
    END $$;
    """))

    # Optionnel (ex: recherche plein texte)
    # op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))


def downgrade() -> None:
    # ordre inverse – idempotent
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_runs_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_runs_started_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_nodes_key"))
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_nodes_run_created_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_artifacts_node_created_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS public.ix_events_run_ts_desc"))
