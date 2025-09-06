from alembic import op
import sqlalchemy as sa

# IDs Alembic
revision = "20240906_add_nodes_role"
down_revision = "d6d12e0cac2a"   # ← ta migration ENUM
branch_labels = None
depends_on = None

def upgrade():
    # Ajoute la colonne si absente (dev/prod safe)
    op.execute("ALTER TABLE nodes ADD COLUMN IF NOT EXISTS role VARCHAR")
    # Index facultatif si tu filtres souvent par role :
    # op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_role ON nodes(role)")

def downgrade():
    # Downgrade simple (optionnel)
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS role")
