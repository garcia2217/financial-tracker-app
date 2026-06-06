from collections import defaultdict
from decimal import Decimal
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


def transaction_effect(
    txn_type: str,
    wallet_id: UUID,
    destination_wallet_id: UUID | None,
    amount: Decimal,
) -> dict[UUID, Decimal]:
    """Balance change a transaction imposes on wallets when applied.

    Expense debits the source; income credits it; a transfer debits the source
    and credits the destination. Pure function — no I/O — so it is unit-testable.
    """
    if txn_type == "expense":
        return {wallet_id: -amount}
    if txn_type == "income":
        return {wallet_id: amount}
    if txn_type == "transfer":
        if destination_wallet_id is None:
            raise AppDomainError("Transfers require a destination_wallet_id")
        return {wallet_id: -amount, destination_wallet_id: amount}
    raise AppDomainError(f"Invalid transaction type: {txn_type}")


def negate_effect(effect: dict[UUID, Decimal]) -> dict[UUID, Decimal]:
    """Reverse a transaction's effect (used to undo an existing transaction)."""
    return {wallet_id: -delta for wallet_id, delta in effect.items()}


def merge_deltas(*effects: dict[UUID, Decimal]) -> dict[UUID, Decimal]:
    """Sum per-wallet deltas, dropping any that net to zero."""
    merged: dict[UUID, Decimal] = defaultdict(Decimal)
    for effect in effects:
        for wallet_id, delta in effect.items():
            merged[wallet_id] += delta
    return {wallet_id: delta for wallet_id, delta in merged.items() if delta != 0}


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

    async def _apply_deltas(self, deltas: dict[UUID, Decimal]) -> None:
        """Apply per-wallet balance changes under row locks.

        Wallets are locked in sorted id order to avoid deadlocks between
        concurrent operations that touch the same set of wallets.
        """
        for wallet_id in sorted(deltas):
            wallet = await self.wallet_repo.get_by_id_for_update(wallet_id)
            if wallet is None:
                raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))
            wallet.balance = wallet.balance + deltas[wallet_id]
            self.session.add(wallet)

    async def _validate_wallet(self, wallet_id: UUID, user_id: UUID) -> None:
        wallet = await self.wallet_repo.get_by_id(wallet_id)
        if not wallet or wallet.user_id != user_id:
            raise ResourceNotFoundError(resource="Wallet", id=str(wallet_id))

    def _validate_transfer(
        self, wallet_id: UUID, destination_wallet_id: UUID | None
    ) -> None:
        if not destination_wallet_id:
            raise AppDomainError("Transfers require a destination_wallet_id")
        if wallet_id == destination_wallet_id:
            raise BusinessRuleViolationError(
                "Source and destination wallet must be different for a transfer"
            )

    async def create_transaction(self, transaction_in: TransactionCreate):
        await self._validate_wallet(transaction_in.wallet_id, transaction_in.user_id)

        if transaction_in.type == "transfer":
            self._validate_transfer(
                transaction_in.wallet_id, transaction_in.destination_wallet_id
            )
            await self._validate_wallet(
                transaction_in.destination_wallet_id, transaction_in.user_id
            )

        deltas = merge_deltas(
            transaction_effect(
                transaction_in.type,
                transaction_in.wallet_id,
                transaction_in.destination_wallet_id,
                transaction_in.amount,
            )
        )
        await self._apply_deltas(deltas)

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

        await self._validate_wallet(update_in.wallet_id, user_id)

        if update_in.type == "transfer":
            self._validate_transfer(update_in.wallet_id, update_in.destination_wallet_id)
            await self._validate_wallet(update_in.destination_wallet_id, user_id)

        # Reverse the old transaction's effect, then apply the new one.
        deltas = merge_deltas(
            negate_effect(
                transaction_effect(
                    txn.type, txn.wallet_id, txn.destination_wallet_id, txn.amount
                )
            ),
            transaction_effect(
                update_in.type,
                update_in.wallet_id,
                update_in.destination_wallet_id,
                update_in.amount,
            ),
        )
        await self._apply_deltas(deltas)

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

        deltas = merge_deltas(
            negate_effect(
                transaction_effect(
                    txn.type, txn.wallet_id, txn.destination_wallet_id, txn.amount
                )
            )
        )
        await self._apply_deltas(deltas)

        await self.session.delete(txn)
        await self.session.commit()
