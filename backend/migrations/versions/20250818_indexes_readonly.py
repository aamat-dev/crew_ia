"""read-only perf indexes (idempotent)"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250818_indexes_readonly"
down_revision = "91570da90011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # events: filtre par run_id + tri timestamp desc
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_run_ts_desc "
        "ON events (run_id, timestamp DESC)"
    )
    # (optionnel) recherche plein texte: nécessite extension pg_trgm créée en amont
    # op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # op.execute(
    #     "CREATE INDEX IF NOT EXISTS ix_events_message_trgm "
    #     "ON events USING gin (message)"
    # )

    # artifacts: liste par node + tri created_at desc
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_artifacts_node_created_desc "
        "ON artifacts (node_id, created_at DESC)"
    )

    # nodes: par run + tri created_at desc, et clé logique
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_nodes_run_created_desc "
        "ON nodes (run_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_nodes_key "
        "ON nodes (key)"
    )

    # runs: tri par started_at desc, filtres courants
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_runs_started_desc "
        "ON runs (started_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_runs_status "
        "ON runs (status)"
    )
    # (optionnel) titre plein texte
    # op.execute(
    #     "CREATE INDEX IF NOT EXISTS ix_runs_title_trgm "
    #     "ON runs USING gin (title)"
    # )


def downgrade() -> None:
    # ordre inverse, et idempotent là aussi
    # op.execute("DROP INDEX IF EXISTS ix_runs_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_runs_status")
    op.execute("DROP INDEX IF EXISTS ix_runs_started_desc")

    op.execute("DROP INDEX IF EXISTS ix_nodes_key")
    op.execute("DROP INDEX IF EXISTS ix_nodes_run_created_desc")

    op.execute("DROP INDEX IF EXISTS ix_artifacts_node_created_desc")

    # op.execute("DROP INDEX IF EXISTS ix_events_message_trgm")
    op.execute("DROP INDEX IF EXISTS ix_events_run_ts_desc")
