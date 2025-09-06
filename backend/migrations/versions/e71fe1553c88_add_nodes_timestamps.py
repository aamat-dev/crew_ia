from alembic import op

# IDs Alembic
revision = "20240906_add_nodes_timestamps"
down_revision = "20240906_add_nodes_role"   # ← la migration précédente
branch_labels = None
depends_on = None

def upgrade():
    # Ajoute les colonnes si absentes (idempotent)
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ")
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ")

    # (optionnel) index si tu fais des tris/filtrages fréquents:
    # op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_created_at ON nodes(created_at)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_updated_at ON nodes(updated_at)")

def downgrade():
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS updated_at")
