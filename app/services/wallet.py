from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
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

    async def update_wallet(self, wallet_id: UUID, wallet_in: WalletUpdate):
        wallet = await self.get_wallet(wallet_id)
        return await self.repo.update(wallet, wallet_in)
