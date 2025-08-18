"""read-only perf indexes"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250818_indexes_readonly"
down_revision = "91570da90011"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # events: filtre par run_id + tri timestamp desc
    op.create_index("ix_events_run_ts_desc", "events", ["run_id", sa.text("timestamp DESC")])
    # (optionnel) recherche plein texte: nécessite extension pg_trgm créée en amont
    # op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # op.create_index("ix_events_message_trgm", "events", [sa.text("message")], postgresql_using="gin")

    # artifacts: liste par node + tri created_at desc
    op.create_index("ix_artifacts_node_created_desc", "artifacts", ["node_id", sa.text("created_at DESC")])

    # nodes: par run + tri created_at desc, et clé logique
    op.create_index("ix_nodes_run_created_desc", "nodes", ["run_id", sa.text("created_at DESC")])
    op.create_index("ix_nodes_key", "nodes", ["key"])

    # runs: tri par started_at desc, filtres courants
    op.create_index("ix_runs_started_desc", "runs", [sa.text("started_at DESC")])
    op.create_index("ix_runs_status", "runs", ["status"])
    # (optionnel) titre plein texte
    # op.create_index("ix_runs_title_trgm", "runs", [sa.text("title")], postgresql_using="gin")

def downgrade() -> None:
    op.drop_index("ix_runs_status", table_name="runs")
    op.drop_index("ix_runs_started_desc", table_name="runs")
    # op.drop_index("ix_runs_title_trgm", table_name="runs")

    op.drop_index("ix_nodes_key", table_name="nodes")
    op.drop_index("ix_nodes_run_created_desc", table_name="nodes")

    op.drop_index("ix_artifacts_node_created_desc", table_name="artifacts")

    # op.drop_index("ix_events_message_trgm", table_name="events")
    op.drop_index("ix_events_run_ts_desc", table_name="events")
