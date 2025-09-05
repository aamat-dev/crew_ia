"""agents unique name-role-domain

Revision ID: c894e2b67dc8
Revises: 129a037b632d
Create Date: 2025-09-05 07:36:02.926573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c894e2b67dc8'
down_revision: Union[str, Sequence[str], None] = '129a037b632d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("uq_agents_name", "agents", type_="unique")
    op.create_unique_constraint(
        "uq_agents_name_role_domain", "agents", ["name", "role", "domain"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_agents_name_role_domain", "agents", type_="unique")
    op.create_unique_constraint("uq_agents_name", "agents", ["name"])
