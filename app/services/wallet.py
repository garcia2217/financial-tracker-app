from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.repositories.wallet import WalletRepository
from app.schemas.wallet import WalletCreate, WalletUpdate


# Matches the index name in the wallets model and its migration. Used to tell a
# name collision apart from the one-default-per-user index, which can also raise
# IntegrityError and must not be reported as a duplicate name.
_NAME_INDEX = "uq_wallets_user_id_lower_name"
_DEFAULT_INDEX = "uq_wallets_one_default_per_user"


def _duplicate_name_error(name: str) -> BusinessRuleViolationError:
    return BusinessRuleViolationError(f"You already have a wallet named '{name}'.")


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
        await self._assert_name_available(wallet_in.user_id, wallet_in.name)
        if not await self.repo.has_wallets(wallet_in.user_id):
            wallet_in = wallet_in.model_copy(update={"is_default": True})
        try:
            return await self.repo.create(wallet_in)
        except IntegrityError as exc:
            await self.session.rollback()
            if _NAME_INDEX not in str(exc.orig):
                raise
            raise _duplicate_name_error(wallet_in.name) from exc

    async def update_wallet(self, wallet_id: UUID, user_id: UUID, wallet_in: WalletUpdate):
        wallet = await self.get_wallet(wallet_id)
        if wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        if wallet_in.name is None:
            return await self.repo.update(wallet, wallet_in)

        await self._assert_name_available(user_id, wallet_in.name, exclude_wallet_id=wallet_id)
        try:
            return await self.repo.update(wallet, wallet_in)
        except IntegrityError as exc:
            await self.session.rollback()
            if _NAME_INDEX not in str(exc.orig):
                raise
            raise _duplicate_name_error(wallet_in.name) from exc

    async def set_default_wallet(self, wallet_id: UUID, user_id: UUID):
        wallet = await self.get_wallet(wallet_id)
        if wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        try:
            return await self.repo.set_default(wallet)
        except IntegrityError as exc:
            await self.session.rollback()
            if _DEFAULT_INDEX not in str(exc.orig):
                raise
            raise BusinessRuleViolationError(
                "Your default wallet was changed by another request. Please try again."
            ) from exc

    async def delete_wallet(self, wallet_id: UUID, user_id: UUID) -> None:
        wallet = await self.get_wallet(wallet_id)
        if wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
        if await self.repo.has_transactions(wallet_id):
            raise BusinessRuleViolationError(
                "Cannot delete a wallet that has associated transactions."
            )
        await self.repo.delete(wallet)

    async def _assert_name_available(
        self, user_id: UUID, name: str, exclude_wallet_id: UUID | None = None
    ) -> None:
        existing = await self.repo.get_user_wallet_by_name(user_id, name, exclude_wallet_id)
        if existing:
            raise _duplicate_name_error(name)
