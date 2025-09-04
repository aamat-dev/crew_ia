"""merge heads

Revision ID: 129a037b632d
Revises: 20250902_01, e3b0c4424d59
Create Date: 2025-09-04 18:38:33.484547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '129a037b632d'
down_revision: Union[str, Sequence[str], None] = ('20250902_01', 'e3b0c4424d59')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
