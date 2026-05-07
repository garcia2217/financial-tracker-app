from collections import defaultdict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppDomainError, ForbiddenError, ResourceNotFoundError
from app.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.repositories.wallet import WalletRepository
from app.schemas.transaction import TransactionCreate, TransactionMonthlySummary, TransactionUpdateRequest


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

    async def get_monthly_summary(self, user_id: UUID, year: int, month: int) -> TransactionMonthlySummary:
        return await self.repo.get_monthly_summary(user_id, year, month)

    async def create_transaction(self, transaction_in: TransactionCreate):
        # --- Validate source wallet ownership and existence ---
        wallet = await self.wallet_repo.get_by_id(transaction_in.wallet_id)
        if not wallet or wallet.user_id != transaction_in.user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(transaction_in.wallet_id))

        if transaction_in.type == "transfer":
            if not transaction_in.destination_wallet_id:
                raise AppDomainError("Transfers require a destination_wallet_id")

            if transaction_in.wallet_id == transaction_in.destination_wallet_id:
                raise BusinessRuleViolationError(
                    "Source and destination wallet must be different for a transfer"
                )

            dest_wallet = await self.wallet_repo.get_by_id(transaction_in.destination_wallet_id)
            if not dest_wallet or dest_wallet.user_id != transaction_in.user_id:
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

    async def update_transaction(
        self, transaction_id: UUID, user_id: UUID, update_in: TransactionUpdateRequest
    ) -> Transaction:
        txn = await self.repo.get_by_id(transaction_id)
        if not txn:
            raise ResourceNotFoundError(resource="Transaction", id=str(transaction_id))
        if txn.user_id != user_id:
            raise ForbiddenError("Transaction belongs to a different user")

        # Validate new source wallet
        new_wallet = await self.wallet_repo.get_by_id(update_in.wallet_id)
        if not new_wallet or new_wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(update_in.wallet_id))

        # Validate transfer-specific rules
        if update_in.type == "transfer":
            if not update_in.destination_wallet_id:
                raise AppDomainError("Transfers require a destination_wallet_id")
            if update_in.wallet_id == update_in.destination_wallet_id:
                raise BusinessRuleViolationError(
                    "Source and destination wallet must be different for a transfer"
                )
            dest_wallet = await self.wallet_repo.get_by_id(update_in.destination_wallet_id)
            if not dest_wallet or dest_wallet.user_id != user_id:
                raise ResourceNotFoundError(
                    resource="Wallet", id=str(update_in.destination_wallet_id)
                )

        # Compute balance deltas: reverse old effect, apply new effect
        deltas: dict[UUID, float] = defaultdict(float)

        if txn.type == "expense":
            deltas[txn.wallet_id] += float(txn.amount)
        elif txn.type == "income":
            deltas[txn.wallet_id] -= float(txn.amount)
        elif txn.type == "transfer":
            deltas[txn.wallet_id] += float(txn.amount)
            if txn.destination_wallet_id:
                deltas[txn.destination_wallet_id] -= float(txn.amount)

        if update_in.type == "expense":
            deltas[update_in.wallet_id] -= update_in.amount
        elif update_in.type == "income":
            deltas[update_in.wallet_id] += update_in.amount
        elif update_in.type == "transfer":
            deltas[update_in.wallet_id] -= update_in.amount
            deltas[update_in.destination_wallet_id] += update_in.amount

        for wallet_id, delta in deltas.items():
            if delta == 0:
                continue
            wallet = await self.wallet_repo.get_by_id(wallet_id)
            if wallet:
                wallet.balance = float(wallet.balance) + delta
                self.session.add(wallet)

        # Update transaction fields in place
        for field, value in update_in.model_dump().items():
            setattr(txn, field, value)
        self.session.add(txn)

        await self.session.commit()
        await self.session.refresh(txn)
        return txn

    async def delete_transaction(self, transaction_id: UUID, user_id: UUID) -> None:
        txn = await self.repo.get_by_id(transaction_id)
        if not txn:
            raise ResourceNotFoundError(resource="Transaction", id=str(transaction_id))
        if txn.user_id != user_id:
            raise ForbiddenError("Transaction belongs to a different user")

        # Reverse balance effects
        if txn.type == "expense":
            wallet = await self.wallet_repo.get_by_id(txn.wallet_id)
            if wallet:
                wallet.balance = float(wallet.balance) + float(txn.amount)
                self.session.add(wallet)
        elif txn.type == "income":
            wallet = await self.wallet_repo.get_by_id(txn.wallet_id)
            if wallet:
                wallet.balance = float(wallet.balance) - float(txn.amount)
                self.session.add(wallet)
        elif txn.type == "transfer":
            wallet = await self.wallet_repo.get_by_id(txn.wallet_id)
            if wallet:
                wallet.balance = float(wallet.balance) + float(txn.amount)
                self.session.add(wallet)
            if txn.destination_wallet_id:
                dest_wallet = await self.wallet_repo.get_by_id(txn.destination_wallet_id)
                if dest_wallet:
                    dest_wallet.balance = float(dest_wallet.balance) - float(txn.amount)
                    self.session.add(dest_wallet)

        await self.session.delete(txn)
        await self.session.commit()
