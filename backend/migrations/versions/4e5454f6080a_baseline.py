"""global min schema patch

Revision ID: 40c0f6d462ff
Revises:
Create Date: 2025-09-06 20:54:37.725631
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# ---- Alembic identifiers ----
revision: str = "40c0f6d462ff"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ------------ helpers -------------
def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    return bool(
        conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": name}).scalar()
    )


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :t AND column_name = :c
                """
            ),
            {"t": table, "c": column},
        ).scalar()
    )


# ------------- upgrade --------------
def upgrade() -> None:
    # Normalise alembic_version column type (sans incidence si déjà OK)
    op.execute(
        "ALTER TABLE IF EXISTS alembic_version "
        "ALTER COLUMN version_num TYPE VARCHAR(255)"
    )

    # ENUMs idempotents
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='agentrole') THEN
            CREATE TYPE agentrole AS ENUM (
              'orchestrator','supervisor','manager','executor','reviewer','recruiter','monitor'
            );
          END IF;

          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='taskstatus') THEN
            CREATE TYPE taskstatus AS ENUM (
              'draft','ready','running','paused','completed','failed'
            );
          END IF;

          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='runstatus') THEN
            CREATE TYPE runstatus AS ENUM (
              'queued','running','completed','failed','canceled'
            );
          END IF;

          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='nodestatus') THEN
            CREATE TYPE nodestatus AS ENUM (
              'queued','running','completed','failed','canceled'
            );
          END IF;

          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='planstatus') THEN
            CREATE TYPE planstatus AS ENUM (
              'draft','ready','invalid'
            );
          END IF;
        END $$;
        """
    )

    # -------- agents --------
    if not _table_exists("agents"):
        op.create_table(
            "agents",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column(
                "role",
                pg.ENUM(
                    "orchestrator",
                    "supervisor",
                    "manager",
                    "executor",
                    "reviewer",
                    "recruiter",
                    "monitor",
                    name="agentrole",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("domain", sa.Text(), nullable=False),
            sa.Column("prompt_system", sa.Text(), nullable=True),
            sa.Column("prompt_user", sa.Text(), nullable=True),
            sa.Column("default_model", sa.Text(), nullable=True),
            sa.Column("config", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column(
                "parent_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("agents.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("name", "role", "domain", name="uq_agents_name_role_domain"),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agents_role_domain ON agents(role, domain)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agents_active ON agents(is_active)")
    # Colonnes manquantes si table déjà existante
    if _table_exists("agents"):
        if not _has_column("agents", "prompt_system"):
            op.add_column("agents", sa.Column("prompt_system", sa.Text(), nullable=True))
        if not _has_column("agents", "prompt_user"):
            op.add_column("agents", sa.Column("prompt_user", sa.Text(), nullable=True))
        if not _has_column("agents", "default_model"):
            op.add_column("agents", sa.Column("default_model", sa.Text(), nullable=True))
        if not _has_column("agents", "config"):
            op.add_column("agents", sa.Column("config", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
        if not _has_column("agents", "version"):
            op.add_column("agents", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    # -------- runs --------
    if not _table_exists("runs"):
        op.create_table(
            "runs",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column(
                "status",
                pg.ENUM(
                    "queued", "running", "completed", "failed", "canceled",
                    name="runstatus",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", pg.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        if not _has_column("runs", "title"):
            op.add_column("runs", sa.Column("title", sa.String(), nullable=False, server_default=""))
            op.execute("ALTER TABLE runs ALTER COLUMN title DROP DEFAULT")
        if not _has_column("runs", "status"):
            op.add_column(
                "runs",
                sa.Column(
                    "status",
                    pg.ENUM("queued", "running", "completed", "failed", "canceled", name="runstatus", create_type=False),
                    nullable=False,
                    server_default="running",
                ),
            )
            op.execute("ALTER TABLE runs ALTER COLUMN status DROP DEFAULT")
        if not _has_column("runs", "started_at"):
            op.add_column("runs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column("runs", "ended_at"):
            op.add_column("runs", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column("runs", "created_at"):
            op.add_column("runs", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
        if not _has_column("runs", "updated_at"):
            op.add_column("runs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_column("runs", "metadata"):
            op.add_column("runs", sa.Column("metadata", pg.JSONB(), nullable=True))

    op.execute("CREATE INDEX IF NOT EXISTS ix_runs_status ON runs(status)")

    # -------- nodes (ajout deps JSONB par défaut []) --------
    if not _table_exists("nodes"):
        op.create_table(
            "nodes",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("key", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column(
                "status",
                pg.ENUM(
                    "queued", "running", "completed", "failed", "canceled",
                    name="nodestatus",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("deps", pg.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("checksum", sa.String(), nullable=True),
            sa.Column(
                "run_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("runs.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        if not _has_column("nodes", "title"):
            op.add_column("nodes", sa.Column("title", sa.String(), nullable=False, server_default=""))
            op.execute("ALTER TABLE nodes ALTER COLUMN title DROP DEFAULT")
        if not _has_column("nodes", "status"):
            op.add_column(
                "nodes",
                sa.Column(
                    "status",
                    pg.ENUM("queued", "running", "completed", "failed", "canceled", name="nodestatus", create_type=False),
                    nullable=False,
                    server_default="queued",
                ),
            )
            op.execute("ALTER TABLE nodes ALTER COLUMN status DROP DEFAULT")
        if not _has_column("nodes", "role"):
            op.add_column("nodes", sa.Column("role", sa.String(), nullable=True))
        if not _has_column("nodes", "deps"):
            op.add_column("nodes", sa.Column("deps", pg.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
        if not _has_column("nodes", "checksum"):
            op.add_column("nodes", sa.Column("checksum", sa.String(), nullable=True))
        if not _has_column("nodes", "run_id"):
            op.add_column("nodes", sa.Column("run_id", pg.UUID(as_uuid=True), nullable=True))
            op.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid = 'nodes'::regclass
                      AND conname = 'fk_nodes_run'
                  ) THEN
                    ALTER TABLE nodes
                      ADD CONSTRAINT fk_nodes_run
                      FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE;
                  END IF;
                END $$;
                """
            )

    op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_key ON nodes(key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_run ON nodes(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nodes_status ON nodes(status)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_nodes_run_key ON nodes(run_id, key)")

    # -------- artifacts --------
    if not _table_exists("artifacts"):
        op.create_table(
            "artifacts",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("node_id", pg.UUID(as_uuid=True), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("path", sa.String(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("metadata", pg.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        if not _has_column("artifacts", "metadata"):
            op.add_column("artifacts", sa.Column("metadata", pg.JSONB(), nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS ix_artifacts_node ON artifacts(node_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_artifacts_type ON artifacts(type)")

    # -------- events --------
    if not _table_exists("events"):
        op.create_table(
            "events",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("node_id", pg.UUID(as_uuid=True), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("level", sa.String(length=50), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("request_id", sa.String(), nullable=True),
            sa.Column("extra", pg.JSONB(), nullable=True),
        )
    else:
        if not _has_column("events", "request_id"):
            op.add_column("events", sa.Column("request_id", sa.String(), nullable=True))
        if not _has_column("events", "extra"):
            op.add_column("events", sa.Column("extra", pg.JSONB(), nullable=True))
        # aligne la nullabilité sur le modèle (run_id et node_id peuvent être NULL)
        op.execute("ALTER TABLE events ALTER COLUMN node_id DROP NOT NULL")
        op.execute("ALTER TABLE events ALTER COLUMN run_id DROP NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_run ON events(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_node ON events(node_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_level ON events(level)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_events_request ON events(request_id)")

    # -------- feedbacks --------
    if not _table_exists("feedbacks"):
        op.create_table(
            "feedbacks",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("node_id", pg.UUID(as_uuid=True), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("reviewer", sa.String(), nullable=True),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("comment", sa.Text(), nullable=False),
            sa.Column("request_id", pg.UUID(as_uuid=True), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("metadata", pg.JSONB(), nullable=True),
            sa.Column("evaluation", pg.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
    else:
        if not _has_column("feedbacks", "request_id"):
            op.add_column("feedbacks", sa.Column("request_id", pg.UUID(as_uuid=True), nullable=True))
        if not _has_column("feedbacks", "role"):
            op.add_column("feedbacks", sa.Column("role", sa.String(), nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_run ON feedbacks(run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_node ON feedbacks(node_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_request ON feedbacks(request_id)")

    # -------- agent_models_matrix --------
    if not _table_exists("agent_models_matrix"):
        op.create_table(
            "agent_models_matrix",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "role",
                pg.ENUM(
                    "orchestrator", "supervisor", "manager", "executor", "reviewer", "recruiter", "monitor",
                    name="agentrole",
                    create_type=False,
                ),
                nullable=True,
            ),
            sa.Column("domain", sa.Text(), nullable=True),
            sa.Column("models", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.UniqueConstraint("role", "domain", name="uq_agent_models_matrix_role_domain"),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_agent_models_matrix_rd ON agent_models_matrix(role, domain)")
    else:
        if not _has_column("agent_models_matrix", "models"):
            op.add_column("agent_models_matrix", sa.Column("models", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
        if not _has_column("agent_models_matrix", "version"):
            op.add_column("agent_models_matrix", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        # l'unicité (role, domain)
        op.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'agent_models_matrix'::regclass
                  AND conname = 'uq_agent_models_matrix_role_domain'
              ) THEN
                ALTER TABLE agent_models_matrix
                  ADD CONSTRAINT uq_agent_models_matrix_role_domain UNIQUE(role, domain);
              END IF;
            END $$;
            """
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_agent_models_matrix_rd ON agent_models_matrix(role, domain)")

    # -------- agent_templates --------
    if not _table_exists("agent_templates"):
        op.create_table(
            "agent_templates",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("role", sa.Text(), nullable=False),
            sa.Column("domain", sa.Text(), nullable=False),
            sa.Column("prompt_system", sa.Text(), nullable=True),
            sa.Column("prompt_user", sa.Text(), nullable=True),
            sa.Column("default_model", sa.Text(), nullable=True),
            sa.Column("config", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("name", name="uq_agent_templates_name"),
        )

    # -------- tasks / deps / logs --------
    if not _table_exists("tasks"):
        op.create_table(
            "tasks",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "status",
                pg.ENUM("draft", "ready", "running", "paused", "completed", "failed", name="taskstatus", create_type=False),
                nullable=False,
            ),
            sa.Column(
                "parent_task_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("tasks.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "assigned_agent_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("agents.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_assigned_agent ON tasks(assigned_agent_id)")
    # Ajouts de colonnes manquantes pour la compat avec les modèles
    if not _has_column("tasks", "plan_id"):
        op.add_column("tasks", sa.Column("plan_id", pg.UUID(as_uuid=True), nullable=True))
    if not _has_column("tasks", "run_id"):
        op.add_column("tasks", sa.Column("run_id", pg.UUID(as_uuid=True), nullable=True))
    if not _has_column("tasks", "updated_at"):
        op.add_column("tasks", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    # FKs seront ajoutées après création de "plans"
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_plan ON tasks(plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_run ON tasks(run_id)")

    if not _table_exists("tasks_dependencies"):
        op.create_table(
            "tasks_dependencies",
            sa.Column("task_id", pg.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("depends_on_id", pg.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_depends_on ON tasks_dependencies(depends_on_id)")

    if not _table_exists("logs"):
        op.create_table(
            "logs",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("level", sa.String(length=50), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("agent_id", pg.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("task_id", pg.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_logs_agent ON logs(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logs_task ON logs(task_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_logs_level ON logs(level)")

    # -------- plans (après tasks) --------
    if not _table_exists("plans"):
        op.create_table(
            "plans",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("task_id", pg.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", pg.ENUM("draft", "ready", "invalid", name="planstatus", create_type=False), nullable=False),
            sa.Column("graph", pg.JSONB(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_plans_task ON plans(task_id)")

    # Après création de "plans", ajouter/garantir les FKs sur tasks
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_tasks_plan') THEN
            ALTER TABLE tasks ADD CONSTRAINT fk_tasks_plan FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_tasks_run') THEN
            ALTER TABLE tasks ADD CONSTRAINT fk_tasks_run FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE SET NULL;
          END IF;
        END $$;
        """
    )

    # -------- assignments --------
    if not _table_exists("assignments"):
        op.create_table(
            "assignments",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("plan_id", pg.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
            sa.Column("node_id", sa.Text(), nullable=False),
            sa.Column("role", sa.Text(), nullable=False),
            sa.Column("agent_id", sa.Text(), nullable=False),
            sa.Column("llm_backend", sa.Text(), nullable=False),
            sa.Column("llm_model", sa.Text(), nullable=False),
            sa.Column("params", pg.JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("plan_id", "node_id", name="uq_assignments_plan_node"),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_assignments_plan_id ON assignments(plan_id)")

    # -------- plan_reviews --------
    if not _table_exists("plan_reviews"):
        op.create_table(
            "plan_reviews",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("plan_id", pg.UUID(as_uuid=True), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("validated", sa.Boolean(), nullable=False),
            sa.Column("errors", pg.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_plan_reviews_plan ON plan_reviews(plan_id)")


# ------------- downgrade --------------
def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_logs_level")
    op.execute("DROP INDEX IF EXISTS ix_logs_task")
    op.execute("DROP INDEX IF EXISTS ix_logs_agent")
    if _table_exists("logs"):
        op.drop_table("logs")

    op.execute("DROP INDEX IF EXISTS ix_tasks_depends_on")
    if _table_exists("tasks_dependencies"):
        op.drop_table("tasks_dependencies")

    op.execute("DROP INDEX IF EXISTS ix_tasks_assigned_agent")
    op.execute("DROP INDEX IF EXISTS ix_tasks_status")
    if _table_exists("tasks"):
        op.drop_table("tasks")

    op.execute("DROP INDEX IF EXISTS ix_agent_models_matrix_rd")
    if _table_exists("agent_models_matrix"):
        op.drop_table("agent_models_matrix")

    op.execute("DROP INDEX IF EXISTS ix_feedbacks_request")
    op.execute("DROP INDEX IF EXISTS ix_feedbacks_node")
    op.execute("DROP INDEX IF EXISTS ix_feedbacks_run")
    if _table_exists("feedbacks"):
        op.drop_table("feedbacks")

    op.execute("DROP INDEX IF EXISTS ix_events_request")
    op.execute("DROP INDEX IF EXISTS ix_events_level")
    op.execute("DROP INDEX IF EXISTS ix_events_node")
    op.execute("DROP INDEX IF EXISTS ix_events_run")
    if _table_exists("events"):
        op.drop_table("events")

    op.execute("DROP INDEX IF EXISTS ix_artifacts_type")
    op.execute("DROP INDEX IF EXISTS ix_artifacts_node")
    if _table_exists("artifacts"):
        op.drop_table("artifacts")

    op.execute("DROP INDEX IF EXISTS uq_nodes_run_key")
    op.execute("DROP INDEX IF EXISTS ix_nodes_status")
    op.execute("DROP INDEX IF EXISTS ix_nodes_run")
    op.execute("DROP INDEX IF EXISTS ix_nodes_key")
    if _table_exists("nodes"):
        op.drop_table("nodes")

    op.execute("DROP INDEX IF EXISTS ix_runs_status")
    if _table_exists("runs"):
        op.drop_table("runs")

    op.execute("DROP INDEX IF EXISTS ix_agents_active")
    op.execute("DROP INDEX IF EXISTS ix_agents_role_domain")
    if _table_exists("agents"):
        op.drop_table("agents")

    op.execute("DROP TYPE IF EXISTS nodestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS runstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agentrole CASCADE")
