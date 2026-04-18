from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppDomainError, ResourceNotFoundError
from app.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.repositories.wallet import WalletRepository
from app.schemas.transaction import TransactionCreate


class BusinessRuleViolationError(AppDomainError):
    """Raised when a request violates a business rule (e.g. same-wallet transfer)."""
    pass


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TransactionRepository(session)
        self.wallet_repo = WalletRepository(session)

    async def get_transaction(self, transaction_id: UUID):
        txn = await self.repo.get_by_id(transaction_id)
        if not txn:
            raise ResourceNotFoundError(resource="Transaction", id=str(transaction_id))
        return txn

    async def get_user_transactions(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        year: int | None = None,
        month: int | None = None,
    ):
        return await self.repo.get_user_transactions(user_id, limit, offset, year=year, month=month)

    async def count_user_transactions(
        self,
        user_id: UUID,
        year: int | None = None,
        month: int | None = None,
    ) -> int:
        return await self.repo.count_user_transactions(user_id, year=year, month=month)

    async def create_transaction(self, transaction_in: TransactionCreate):
        # --- Validate source wallet ownership and existence ---
        wallet = await self.wallet_repo.get_by_id(transaction_in.wallet_id)
        if not wallet:
            raise ResourceNotFoundError(resource="Wallet", id=str(transaction_in.wallet_id))

        if transaction_in.type == "transfer":
            if not transaction_in.destination_wallet_id:
                raise AppDomainError("Transfers require a destination_wallet_id")

            if transaction_in.wallet_id == transaction_in.destination_wallet_id:
                raise BusinessRuleViolationError(
                    "Source and destination wallet must be different for a transfer"
                )

            dest_wallet = await self.wallet_repo.get_by_id(transaction_in.destination_wallet_id)
            if not dest_wallet:
                raise ResourceNotFoundError(
                    resource="Wallet", id=str(transaction_in.destination_wallet_id)
                )

            # Update both wallets in memory — no commit yet
            wallet.balance = float(wallet.balance) - transaction_in.amount
            dest_wallet.balance = float(dest_wallet.balance) + transaction_in.amount
            self.session.add(wallet)
            self.session.add(dest_wallet)

        elif transaction_in.type == "expense":
            wallet.balance = float(wallet.balance) - transaction_in.amount
            self.session.add(wallet)

        elif transaction_in.type == "income":
            wallet.balance = float(wallet.balance) + transaction_in.amount
            self.session.add(wallet)

        else:
            raise AppDomainError(f"Invalid transaction type: {transaction_in.type}")

        # Add transaction record — no commit yet
        db_transaction = Transaction(**transaction_in.model_dump(exclude_unset=True))
        self.session.add(db_transaction)

        # Single atomic commit covers wallet update(s) + transaction insert
        await self.session.commit()
        await self.session.refresh(db_transaction)
        return db_transaction
