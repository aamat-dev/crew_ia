"""unicité run_id, key pour nodes"""

from alembic import op

# Identifiants Alembic
revision = "20240905_nodes_run_key_unique"
down_revision = "c894e2b67dc8"  # <-- ajustez si besoin
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Normalise d'abord les doublons éventuels (évite l'échec lors de la création de la contrainte)
    op.execute(
        """
        WITH d AS (
            SELECT ctid, run_id, key,
                   ROW_NUMBER() OVER (PARTITION BY run_id, key ORDER BY id) AS rn
            FROM nodes
            WHERE key IS NOT NULL
        )
        UPDATE nodes n
        SET key = n.key || '__' || substr(n.id::text,1,8)
        FROM d
        WHERE n.ctid = d.ctid AND d.rn > 1;
        """
    )

    # Contrainte d’unicité (run_id, key)
    op.create_unique_constraint("uq_nodes_run_key", "nodes", ["run_id", "key"])


def downgrade() -> None:
    op.drop_constraint("uq_nodes_run_key", "nodes", type_="unique")
