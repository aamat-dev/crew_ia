"""add tasks plans assignments

Revision ID: 7eb39369039a
Revises: 9e95f732b6c3
Create Date: 2025-08-31 18:45:55.674257

Note: les colonnes ``updated_at`` sont gérées par l'ORM via ``onupdate=func.now()``
et non par un trigger base de données.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7eb39369039a'
down_revision: Union[str, Sequence[str], None] = '9e95f732b6c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    taskstatus = postgresql.ENUM(
        "draft",
        "ready",
        "running",
        "paused",
        "completed",
        "failed",
        name="taskstatus",
    )
    planstatus = postgresql.ENUM("draft", "ready", "invalid", name="planstatus")

    bind = op.get_bind()
    taskstatus.create(bind, checkfirst=True)
    planstatus.create(bind, checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="taskstatus", create_type=False),
            nullable=False,
        ),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="SET NULL"),
    )
    op.execute(
        "CREATE INDEX ix_tasks_status_created_at_desc ON tasks (status, created_at DESC)"
    )

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="planstatus", create_type=False),
            nullable=False,
        ),
        sa.Column("graph", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "version", sa.Integer(), server_default="1", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_plans_task_id", "plans", ["task_id"], unique=False)

    op.create_foreign_key(
        "fk_tasks_plan_id_plans",
        "tasks",
        "plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.Text(), nullable=False),
        sa.Column("llm_backend", sa.Text(), nullable=False),
        sa.Column("llm_model", sa.Text(), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("plan_id", "node_id", name="uq_assignments_plan_node"),
    )
    op.create_index(
        "ix_assignments_plan_id", "assignments", ["plan_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_assignments_plan_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_constraint("fk_tasks_plan_id_plans", "tasks", type_="foreignkey")

    op.drop_index("ix_plans_task_id", table_name="plans")
    op.drop_table("plans")

    op.execute("DROP INDEX IF EXISTS ix_tasks_status_created_at_desc")
    op.drop_table("tasks")

    bind = op.get_bind()
    planstatus = postgresql.ENUM(
        "draft", "ready", "invalid", name="planstatus"
    )
    taskstatus = postgresql.ENUM(
        "draft",
        "ready",
        "running",
        "paused",
        "completed",
        "failed",
        name="taskstatus",
    )
    planstatus.drop(bind, checkfirst=True)
    taskstatus.drop(bind, checkfirst=True)
