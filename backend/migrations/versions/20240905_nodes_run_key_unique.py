from alembic import op


revision = "20240905_nodes_run_key_unique"
down_revision = "129a037b632d"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_unique_constraint("uq_nodes_run_key", "nodes", ["run_id", "key"])


def downgrade() -> None:
    op.drop_constraint("uq_nodes_run_key", "nodes", type_="unique")
