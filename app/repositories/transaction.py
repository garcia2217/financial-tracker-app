from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        result = await self.session.execute(select(Transaction).where(Transaction.id == transaction_id))
        return result.scalars().first()

    async def get_user_transactions(self, user_id: UUID, limit: int = 50, offset: int = 0) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_user_transactions(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        )
        return result.scalar_one()

    async def create(self, transaction_in: TransactionCreate) -> Transaction:
        # Note: business logic like updating the wallet balance belongs in the Service layer, not the Repository
        db_transaction = Transaction(**transaction_in.model_dump(exclude_unset=True))
        self.session.add(db_transaction)
        await self.session.commit()
        await self.session.refresh(db_transaction)
        return db_transaction
