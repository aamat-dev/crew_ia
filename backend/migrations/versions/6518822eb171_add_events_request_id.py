from alembic import op

# IDs Alembic
revision = "6518822eb171"
down_revision = "20240906_add_nodes_timestamps"  # ← ta précédente migration
branch_labels = None
depends_on = None

def upgrade():
    # Colonne pour tracer l'ID de requête (header X-Request-ID)
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS request_id VARCHAR")
    # Index utile si tu filtres par request_id / requêtes récentes
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_request_id ON events(request_id)")

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_events_request_id")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS request_id")
