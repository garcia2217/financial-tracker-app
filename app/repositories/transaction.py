from uuid import UUID
from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionMonthlySummary


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        result = await self.session.execute(select(Transaction).where(Transaction.id == transaction_id))
        return result.scalars().first()

    async def get_user_transactions(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        year: int | None = None,
        month: int | None = None,
    ) -> Sequence[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if year is not None and month is not None:
            stmt = stmt.where(
                extract("year", Transaction.transaction_date) == year,
                extract("month", Transaction.transaction_date) == month,
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_user_transactions(
        self,
        user_id: UUID,
        year: int | None = None,
        month: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        if year is not None and month is not None:
            stmt = stmt.where(
                extract("year", Transaction.transaction_date) == year,
                extract("month", Transaction.transaction_date) == month,
            )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_monthly_summary(self, user_id: UUID, year: int, month: int) -> TransactionMonthlySummary:
        stmt = select(
            func.coalesce(
                func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)), 0
            ).label("total_income"),
            func.coalesce(
                func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)), 0
            ).label("total_expense"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.type != "transfer",
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
        result = await self.session.execute(stmt)
        row = result.one()
        return TransactionMonthlySummary(totalIncome=float(row.total_income), totalExpense=float(row.total_expense))

    async def create(self, transaction_in: TransactionCreate) -> Transaction:
        # Note: business logic like updating the wallet balance belongs in the Service layer, not the Repository
        db_transaction = Transaction(**transaction_in.model_dump(exclude_unset=True))
        self.session.add(db_transaction)
        await self.session.commit()
        await self.session.refresh(db_transaction)
        return db_transaction
