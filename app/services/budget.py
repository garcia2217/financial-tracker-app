from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository
from app.schemas.budget import BudgetCreate, BudgetCreateRequest, BudgetUpdate


class BudgetService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BudgetRepository(session)
        self.category_repo = CategoryRepository(session)

    async def get_effective_budgets(self, user_id: UUID, year: int, month: int):
        defaults = await self.repo.get_user_defaults(user_id)
        overrides = await self.repo.get_user_overrides_for_month(user_id, year, month)

        # Build dict keyed by category_id; overrides win over defaults
        merged: dict = {b.category_id: b for b in defaults}
        for override in overrides:
            merged[override.category_id] = override

        return list(merged.values())

    async def create_budget(self, user_id: UUID, body: BudgetCreateRequest):
        # Verify the category exists
        category = await self.category_repo.get_by_id(body.category_id)
        if not category:
            raise ResourceNotFoundError(resource="Category", id=str(body.category_id))

        # Guard against duplicate defaults per category
        if body.is_default:
            existing = await self.repo.get_default_by_category(user_id, body.category_id)
            if existing:
                raise BusinessRuleViolationError(
                    "A default budget already exists for this category."
                )

        budget_in = BudgetCreate(user_id=user_id, **body.model_dump())
        return await self.repo.create(budget_in)

    async def update_budget(self, budget_id: UUID, user_id: UUID, amount: float):
        budget = await self.repo.get_by_id_for_user(budget_id, user_id)
        if not budget:
            raise ResourceNotFoundError(resource="Budget", id=str(budget_id))
        return await self.repo.update(budget, BudgetUpdate(amount=amount))

    async def delete_budget(self, budget_id: UUID, user_id: UUID) -> None:
        budget = await self.repo.get_by_id_for_user(budget_id, user_id)
        if not budget:
            raise ResourceNotFoundError(resource="Budget", id=str(budget_id))
        await self.repo.delete(budget)
