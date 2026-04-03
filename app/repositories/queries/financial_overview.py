from uuid import UUID
from sqlalchemy import select, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from decimal import Decimal
from app.models import Category, Transaction, Wallet, Debt
from app.schemas import FinancialOverview, TransactionOverview

class FinancialOverviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_financial_overview(self, user_id: UUID, month: int, year: int) -> FinancialOverview:
        """
        Gathers a full financial overview for a user.
        Combines recent transactions, balances, and monthly aggregates.
        """
        # 1. Fetch data components in parallel if possible, 
        # but for now, we'll keep it sequential for clarity.
        recent_txs = await self._get_recent_transactions(user_id)
        assets = await self._get_total_assets(user_id)
        liabilities = await self._get_total_liabilities(user_id)
        stats = await self._get_monthly_stats(user_id, month, year)

        # 2. Calculate business logic (Savings Rate)
        income = stats["income"]
        expense = stats["expense"]
        savings_rate = 0.0
        if income > 0:
            savings_rate = float(((income - expense) / income) * 100)

        return FinancialOverview(
            transactions=recent_txs,
            total_assets=assets,
            total_liabilities=liabilities,
            monthly_income=income,
            monthly_expense=expense,
            savings_rate=round(savings_rate, 2)
        )
        
    async def _get_recent_transactions(self, user_id: UUID) -> List[TransactionOverview]:
        stmt = (
            select(
                Category.name.label("category_name"),
                Transaction.type,
                Transaction.amount,
                Transaction.transaction_date,
                Transaction.description,
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
            .limit(5)
        )
        result = await self.session.execute(stmt)
        return [TransactionOverview(**row) for row in result.mappings()]

    async def _get_total_assets(self, user_id: UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(Wallet.balance), 0)).where(
            Wallet.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or Decimal("0.00")

    async def _get_total_liabilities(self, user_id: UUID) -> Decimal:
        # Debt logic: amount - amount_settled
        stmt = select(
            func.coalesce(func.sum(Debt.amount - Debt.amount_settled), 0)
        ).where(
            Debt.user_id == user_id,
            Debt.type == "payable",
            Debt.status != "settled"
        )
        result = await self.session.execute(stmt)
        return result.scalar() or Decimal("0.00")

    async def _get_monthly_stats(self, user_id: UUID, month: int, year: int) -> dict:
        income_case = case((Transaction.type == "income", Transaction.amount), else_=0)
        expense_case = case((Transaction.type == "expense", Transaction.amount), else_=0)

        stmt = (
            select(
                func.coalesce(func.sum(income_case), 0).label("income"),
                func.coalesce(func.sum(expense_case), 0).label("expense"),
            )
            .where(
                Transaction.user_id == user_id,
                extract("month", Transaction.transaction_date) == month,
                extract("year", Transaction.transaction_date) == year,
            )
        )
        result = await self.session.execute(stmt)
        return result.mappings().one()
