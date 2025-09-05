from alembic import op

revision = "20240905_nodes_run_key_unique"
down_revision = "129a037b632d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_nodes_run_key", "nodes", ["run_id", "key"]
    )


def downgrade():
    op.drop_constraint("uq_nodes_run_key", "nodes", type_="unique")
