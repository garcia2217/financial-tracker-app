from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletUpdate

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        result = await self.session.execute(select(Wallet).where(Wallet.id == wallet_id))
        return result.scalars().first()

    async def get_user_wallets(self, user_id: UUID) -> Sequence[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return result.scalars().all()

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
