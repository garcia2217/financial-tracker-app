from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.repositories.wallet import WalletRepository
from app.schemas.wallet import WalletCreate, WalletUpdate


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WalletRepository(session)

    async def get_wallet(self, wallet_id: UUID):
        wallet = await self.repo.get_by_id(wallet_id)
        if not wallet:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        return wallet

    async def get_user_wallets(self, user_id: UUID):
        return await self.repo.get_user_wallets(user_id)

    async def create_wallet(self, wallet_in: WalletCreate):
        return await self.repo.create(wallet_in)

    async def update_wallet(self, wallet_id: UUID, user_id: UUID, wallet_in: WalletUpdate):
        wallet = await self.get_wallet(wallet_id)
        if wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        return await self.repo.update(wallet, wallet_in)

    async def delete_wallet(self, wallet_id: UUID, user_id: UUID) -> None:
        wallet = await self.get_wallet(wallet_id)
        if wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        if await self.repo.has_transactions(wallet_id):
            raise BusinessRuleViolationError(
                "Cannot delete a wallet that has associated transactions."
            )
        await self.repo.delete(wallet)
