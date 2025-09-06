from alembic import op
import sqlalchemy as sa

# Remplace par l’ID auto-généré par Alembic
revision = '188976e12962'
down_revision = '83c6c56308fb'
branch_labels = None
depends_on = None

def upgrade():
    # Au cas où, on crée les colonnes si elles n’existent pas (idempotent)
    op.execute("""
        ALTER TABLE runs
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ
    """)
    # Défauts pour les insertions futures
    op.execute("ALTER TABLE runs ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE runs ALTER COLUMN updated_at SET DEFAULT now()")
    # Rétro-remplissage (si des lignes existent déjà)
    op.execute("""
        UPDATE runs
        SET created_at = COALESCE(created_at, now()),
            updated_at = COALESCE(updated_at, now())
    """)
    # Contrainte forte (optionnel : laisse si tu veux le NOT NULL)
    op.execute("ALTER TABLE runs ALTER COLUMN created_at SET NOT NULL")
    op.execute("ALTER TABLE runs ALTER COLUMN updated_at SET NOT NULL")

def downgrade():
    # On retire juste les contraintes/défauts ; on évite de dropper les colonnes
    op.execute("ALTER TABLE runs ALTER COLUMN updated_at DROP NOT NULL")
    op.execute("ALTER TABLE runs ALTER COLUMN updated_at DROP DEFAULT")
    op.execute("ALTER TABLE runs ALTER COLUMN created_at DROP NOT NULL")
    op.execute("ALTER TABLE runs ALTER COLUMN created_at DROP DEFAULT")
