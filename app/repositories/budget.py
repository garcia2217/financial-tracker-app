from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate

class BudgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, budget_id: UUID) -> Budget | None:
        result = await self.session.execute(select(Budget).where(Budget.id == budget_id))
        return result.scalars().first()

    async def get_user_budgets(self, user_id: UUID) -> Sequence[Budget]:
        result = await self.session.execute(select(Budget).where(Budget.user_id == user_id))
        return result.scalars().all()

    async def create(self, budget_in: BudgetCreate) -> Budget:
        db_budget = Budget(**budget_in.model_dump(exclude_unset=True))
        self.session.add(db_budget)
        await self.session.commit()
        await self.session.refresh(db_budget)
        return db_budget

    async def update(self, db_budget: Budget, budget_in: BudgetUpdate) -> Budget:
        update_data = budget_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_budget, field, value)
        self.session.add(db_budget)
        await self.session.commit()
        await self.session.refresh(db_budget)
        return db_budget
