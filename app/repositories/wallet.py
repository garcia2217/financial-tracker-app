from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletUpdate

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        result = await self.session.execute(select(Wallet).where(Wallet.id == wallet_id))
        return result.scalars().first()

    async def get_by_id_for_update(self, wallet_id: UUID) -> Wallet | None:
        """Fetch a wallet with a row-level lock (SELECT ... FOR UPDATE).

        populate_existing forces a refresh from the locked row, so the caller
        never operates on a stale balance left in the identity map by an earlier
        read. This is what makes the balance update safe under concurrency.
        """
        result = await self.session.execute(
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return result.scalars().first()

    async def get_user_wallets(self, user_id: UUID) -> Sequence[Wallet]:
        result = await self.session.execute(
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .order_by(Wallet.created_at, Wallet.id)
        )
        return result.scalars().all()

    async def get_user_wallet_by_name(
        self, user_id: UUID, name: str, exclude_wallet_id: UUID | None = None
    ) -> Wallet | None:
        """Look up a wallet by name, matching the case-insensitive uniqueness the DB enforces."""
        stmt = select(Wallet).where(
            Wallet.user_id == user_id,
            func.lower(Wallet.name) == name.lower(),
        )
        if exclude_wallet_id is not None:
            stmt = stmt.where(Wallet.id != exclude_wallet_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, wallet_in: WalletCreate) -> Wallet:
        db_wallet = Wallet(**wallet_in.model_dump(exclude_unset=True))
        self.session.add(db_wallet)
        await self.session.commit()
        await self.session.refresh(db_wallet)
        return db_wallet

    async def update(self, db_wallet: Wallet, wallet_in: WalletUpdate) -> Wallet:
        update_data = wallet_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_wallet, field, value)
        self.session.add(db_wallet)
        await self.session.commit()
        await self.session.refresh(db_wallet)
        return db_wallet

    async def has_transactions(self, wallet_id: UUID) -> bool:
        result = await self.session.execute(
            select(Transaction.id).where(Transaction.wallet_id == wallet_id).limit(1)
        )
        return result.scalars().first() is not None

    async def delete(self, db_wallet: Wallet) -> None:
        await self.session.delete(db_wallet)
        await self.session.commit()
