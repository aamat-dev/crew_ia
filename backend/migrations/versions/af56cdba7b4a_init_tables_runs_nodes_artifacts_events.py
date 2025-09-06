"""init tables: runs, nodes, artifacts, events

Revision ID: af56cdba7b4a
Revises:
Create Date: 2025-08-16 20:02:19.353692
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401 (kept for parity with autogen headers)
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "af56cdba7b4a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create ENUM types if they don't exist (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='runstatus') THEN
                CREATE TYPE runstatus AS ENUM ('pending','running','succeeded','failed','cancelled');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='nodestatus') THEN
                CREATE TYPE nodestatus AS ENUM ('pending','running','succeeded','failed','skipped','cancelled');
            END IF;
        END $$;
        """
    )

    # runs
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "succeeded",
                "failed",
                "cancelled",
                name="runstatus",
                create_type=False,  # <- don't auto-create; we did it above
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runs_ended_at"), "runs", ["ended_at"], unique=False)
    op.create_index(op.f("ix_runs_id"), "runs", ["id"], unique=False)
    op.create_index(op.f("ix_runs_started_at"), "runs", ["started_at"], unique=False)
    op.create_index(op.f("ix_runs_title"), "runs", ["title"], unique=False)

    # nodes
    op.create_table(
        "nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "succeeded",
                "failed",
                "skipped",
                "cancelled",
                name="nodestatus",
                create_type=False,  # <- don't auto-create; we did it above
            ),
            nullable=False,
        ),
        sa.Column("deps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nodes_checksum"), "nodes", ["checksum"], unique=False)
    op.create_index(op.f("ix_nodes_ended_at"), "nodes", ["ended_at"], unique=False)
    op.create_index(op.f("ix_nodes_id"), "nodes", ["id"], unique=False)
    op.create_index(op.f("ix_nodes_run_id"), "nodes", ["run_id"], unique=False)
    op.create_index(op.f("ix_nodes_started_at"), "nodes", ["started_at"], unique=False)
    op.create_index(op.f("ix_nodes_status"), "nodes", ["status"], unique=False)
    op.create_index(op.f("ix_nodes_title"), "nodes", ["title"], unique=False)

    # artifacts
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifacts_created_at"), "artifacts", ["created_at"], unique=False)
    op.create_index(op.f("ix_artifacts_id"), "artifacts", ["id"], unique=False)
    op.create_index(op.f("ix_artifacts_node_id"), "artifacts", ["node_id"], unique=False)
    op.create_index(op.f("ix_artifacts_type"), "artifacts", ["type"], unique=False)

    # events
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("node_id", sa.Uuid(), nullable=True),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)
    op.create_index(op.f("ix_events_level"), "events", ["level"], unique=False)
    op.create_index(op.f("ix_events_node_id"), "events", ["node_id"], unique=False)
    op.create_index(op.f("ix_events_run_id"), "events", ["run_id"], unique=False)
    op.create_index(op.f("ix_events_timestamp"), "events", ["timestamp"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_events_timestamp"), table_name="events")
    op.drop_index(op.f("ix_events_run_id"), table_name="events")
    op.drop_index(op.f("ix_events_node_id"), table_name="events")
    op.drop_index(op.f("ix_events_level"), table_name="events")
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_table("events")

    op.drop_index(op.f("ix_artifacts_type"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_node_id"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_id"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_created_at"), table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index(op.f("ix_nodes_title"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_status"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_started_at"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_run_id"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_id"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_ended_at"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_checksum"), table_name="nodes")
    op.drop_table("nodes")

    op.drop_index(op.f("ix_runs_title"), table_name="runs")
    op.drop_index(op.f("ix_runs_started_at"), table_name="runs")
    op.drop_index(op.f("ix_runs_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_ended_at"), table_name="runs")
    op.drop_table("runs")
