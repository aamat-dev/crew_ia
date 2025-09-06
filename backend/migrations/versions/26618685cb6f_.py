"""empty message

Revision ID: 26618685cb6f
Revises: 188976e12962, 9a2f0e1c9cde
Create Date: 2025-09-06 16:40:34.400496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26618685cb6f'
down_revision: Union[str, Sequence[str], None] = ('188976e12962', '9a2f0e1c9cde')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
