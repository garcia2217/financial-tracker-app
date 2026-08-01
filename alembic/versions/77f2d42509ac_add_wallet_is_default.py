"""add_wallet_is_default

Revision ID: 77f2d42509ac
Revises: 49d8fc5a49e3
Create Date: 2026-08-01 16:21:00.616814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77f2d42509ac'
down_revision: Union[str, Sequence[str], None] = '49d8fc5a49e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "wallets",
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Backfill before the index exists: the oldest wallet becomes the default,
    # matching the order get_user_wallets returns.
    op.execute("""
        WITH ranked AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY user_id ORDER BY created_at, id
                   ) AS rn
            FROM wallets
        )
        UPDATE wallets w
        SET is_default = true
        FROM ranked
        WHERE w.id = ranked.id AND ranked.rn = 1
    """)
    op.create_index(
        "uq_wallets_one_default_per_user",
        "wallets",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_wallets_one_default_per_user", table_name="wallets")
    op.drop_column("wallets", "is_default")
