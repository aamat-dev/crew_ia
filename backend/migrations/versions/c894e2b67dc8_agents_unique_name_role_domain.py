"""agents unique name-role-domain

Revision ID: c894e2b67dc8
Revises: 129a037b632d
Create Date: 2025-09-05 07:36:02.926573
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# --- Alembic identifiers ---
revision: str = "c894e2b67dc8"
down_revision: Union[str, Sequence[str], None] = "129a037b632d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Helpers (PostgreSQL) ---
def _table_exists(conn, name: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT to_regclass(:n) IS NOT NULL"),
            {"n": f"public.{name}"},
        ).scalar()
    )


def _constraint_exists(conn, table: str, constraint_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                WHERE t.relname = :t AND c.conname = :n
                """
            ),
            {"t": table, "n": constraint_name},
        ).scalar()
    )


def _index_exists(conn, index_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT 1
                FROM pg_class
                WHERE relkind IN ('i','I') AND relname = :n
                """
            ),
            {"n": index_name},
        ).scalar()
    )


# --- Migration steps ---
def upgrade() -> None:
    """Upgrade schema (idempotent)."""
    conn = op.get_bind()

    # Sécurité: si la table n'existe pas (chemin de migration alternatif), on sort proprement.
    if not _table_exists(conn, "agents"):
        return

    # 1) Drop éventuel de l'ancienne contrainte unique sur (name)
    if _constraint_exists(conn, "agents", "uq_agents_name"):
        op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS uq_agents_name")

    # 2) Créer (si absent) un UNIQUE INDEX stable sur (name, role, domain)
    if not _index_exists(conn, "ux_agents_name_role_domain"):
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_agents_name_role_domain "
            "ON agents (name, role, domain)"
        )

    # 3) Ajouter (si absente) la contrainte unique nommée en s'appuyant sur l'index
    if not _constraint_exists(conn, "agents", "uq_agents_name_role_domain"):
        # Si un autre unique EXISTE déjà sur ces colonnes avec un nom différent,
        # cette commande échouera. Pour rester robuste, on ne tente l'opération
        # que si notre contrainte cible est absente.
        op.execute(
            "ALTER TABLE agents "
            "ADD CONSTRAINT uq_agents_name_role_domain "
            "UNIQUE USING INDEX ux_agents_name_role_domain"
        )


def downgrade() -> None:
    """Downgrade schema (idempotent)."""
    conn = op.get_bind()

    if not _table_exists(conn, "agents"):
        return

    # 1) Supprimer la contrainte composite si elle existe
    if _constraint_exists(conn, "agents", "uq_agents_name_role_domain"):
        op.execute(
            "ALTER TABLE agents DROP CONSTRAINT IF EXISTS uq_agents_name_role_domain"
        )

    # 2) Supprimer l'index (si laissé orphelin)
    if _index_exists(conn, "ux_agents_name_role_domain"):
        op.execute("DROP INDEX IF EXISTS ux_agents_name_role_domain")

    # 3) Restaurer l'ancienne contrainte unique sur (name) si absente
    if not _constraint_exists(conn, "agents", "uq_agents_name"):
        op.execute(
            "ALTER TABLE agents ADD CONSTRAINT uq_agents_name UNIQUE (name)"
        )
