"""add pragmatic indexes on runs/events/nodes

Revision ID: c7a5b1d9cafe
Revises: ab12cd34ef56
Create Date: 2025-09-15 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c7a5b1d9cafe"
down_revision: Union[str, Sequence[str], None] = "ab12cd34ef56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(conn, index_name: str) -> bool:
    row = conn.execute(sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": index_name}).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()

    # runs.created_at
    if not _index_exists(conn, "public.runs_created_at_idx"):
        op.create_index("runs_created_at_idx", "runs", ["created_at"], unique=False)

    # runs.started_at
    if not _index_exists(conn, "public.runs_started_at_idx"):
        op.create_index("runs_started_at_idx", "runs", ["started_at"], unique=False)

    # nodes.run_id (malgré la contrainte unique (run_id,key), index dédié utile pour scans)
    if not _index_exists(conn, "public.nodes_run_id_idx"):
        op.create_index("nodes_run_id_idx", "nodes", ["run_id"], unique=False)

    # events.timestamp seul (tri fréquent)
    if not _index_exists(conn, "public.events_timestamp_idx"):
        op.create_index("events_timestamp_idx", "events", ["timestamp"], unique=False)

    # events (run_id, timestamp) pour filtrage + ordre
    if not _index_exists(conn, "public.events_run_id_timestamp_idx"):
        op.create_index(
            "events_run_id_timestamp_idx",
            "events",
            ["run_id", "timestamp"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    # Suppression prudente
    if _index_exists(conn, "public.events_run_id_timestamp_idx"):
        op.drop_index("events_run_id_timestamp_idx", table_name="events")
    if _index_exists(conn, "public.events_timestamp_idx"):
        op.drop_index("events_timestamp_idx", table_name="events")
    if _index_exists(conn, "public.nodes_run_id_idx"):
        op.drop_index("nodes_run_id_idx", table_name="nodes")
    if _index_exists(conn, "public.runs_started_at_idx"):
        op.drop_index("runs_started_at_idx", table_name="runs")
    if _index_exists(conn, "public.runs_created_at_idx"):
        op.drop_index("runs_created_at_idx", table_name="runs")

