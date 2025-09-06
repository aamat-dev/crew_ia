"""merge heads

Revision ID: 3998bc48da90
Revises: c894e2b67dc8, 20240907_node_key_not_null
Create Date: 2025-09-05 20:06:37.022548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3998bc48da90'
down_revision: Union[str, Sequence[str], None] = (
    'c894e2b67dc8',
    '20240907_node_key_not_null',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
