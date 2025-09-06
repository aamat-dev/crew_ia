from alembic import op
from sqlalchemy import text

revision = "9a2f0e1c9cde"
down_revision = "83c6c56308fb"
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()

    def exists(name: str) -> bool:
        return bool(conn.execute(text("SELECT to_regclass(:n) IS NOT NULL"), {"n": name}).scalar())

    # nodes.key nullable
    if exists("nodes"):
        op.execute("ALTER TABLE nodes ALTER COLUMN key DROP NOT NULL")

    # plan_reviews minimale
    if not exists("plan_reviews"):
        op.execute(
            """
        CREATE TABLE plan_reviews (
            id UUID PRIMARY KEY,
            plan_id UUID NOT NULL,
            version INTEGER NOT NULL,
            validated BOOLEAN NOT NULL,
            errors JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
        """
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_plan_reviews_plan_id ON plan_reviews(plan_id)"
        )
        # FK optionnelle si 'plans' existe
        if exists("plans"):
            op.execute(
                """
            ALTER TABLE plan_reviews
            ADD CONSTRAINT fk_plan_reviews_plan
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
            """
            )
    # sécuriser alembic_version si pas déjà fait
    op.execute(
        "ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"
    )

def downgrade():
    pass
