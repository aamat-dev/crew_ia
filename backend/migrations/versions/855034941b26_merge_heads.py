"""merge heads

Revision ID: 855034941b26
Revises: 20240909_feedbacks_jsonb, 3998bc48da90
Create Date: 2025-09-06 09:53:26.381428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '855034941b26'
down_revision: Union[str, Sequence[str], None] = ('20240909_feedbacks_jsonb', '3998bc48da90')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
