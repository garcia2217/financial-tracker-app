"""make_categories_user_id_nullable

Revision ID: 1f84ff618758
Revises: 5fe6fd444829
Create Date: 2026-04-18 19:30:20.321974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f84ff618758'
down_revision: Union[str, Sequence[str], None] = '5fe6fd444829'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("categories", "user_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("categories", "user_id", existing_type=sa.UUID(), nullable=False)
