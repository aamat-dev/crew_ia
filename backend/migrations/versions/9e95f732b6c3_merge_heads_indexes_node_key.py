"""merge heads: indexes + node.key

Revision ID: 9e95f732b6c3
Revises: 20250818_indexes_readonly, 64f7dcc41f91
Create Date: 2025-08-18 10:36:42.928504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e95f732b6c3'
down_revision: Union[str, Sequence[str], None] = ('20250818_indexes_readonly', '64f7dcc41f91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
