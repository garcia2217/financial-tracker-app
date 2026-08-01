"""add_unique_wallet_name_per_user

Revision ID: 49d8fc5a49e3
Revises: bd36e690e3eb
Create Date: 2026-08-01 16:03:20.113984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49d8fc5a49e3'
down_revision: Union[str, Sequence[str], None] = 'bd36e690e3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        WITH ranked AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY user_id, lower(name)
                       ORDER BY created_at, id
                   ) AS rn
            FROM wallets
        )
        UPDATE wallets w
        SET name = left(w.name, 90) || ' (' || ranked.rn || ')'
        FROM ranked
        WHERE w.id = ranked.id AND ranked.rn > 1
    """)
    op.create_index(
        "uq_wallets_user_id_lower_name",
        "wallets",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_wallets_user_id_lower_name", table_name="wallets")
