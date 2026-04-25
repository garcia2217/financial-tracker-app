from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.core.exceptions import AppDomainError, ResourceNotFoundError
from app.models.debt import Debt
from app.repositories.debt import DebtRepository
from app.repositories.person import PersonRepository
from app.schemas.debt import DebtCreate, DebtCreateRequest, DebtUpdate


class BusinessRuleViolationError(AppDomainError):
    """Raised when a request violates a business rule (e.g. amount_settled exceeds amount)."""
    pass


def _derive_status(amount_settled: float, amount: float) -> str:
    if amount_settled <= 0:
        return "pending"
    if amount_settled >= amount:
        return "settled"
    return "partial"


class DebtService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DebtRepository(session)
        self.person_repo = PersonRepository(session)

    async def get_user_debts(self, user_id: UUID) -> Sequence[Debt]:
        return await self.repo.get_user_debts(user_id)

    async def create_debt(self, user_id: UUID, body: DebtCreateRequest) -> Debt:
        person = await self.person_repo.get_by_id(body.person_id)
        if not person or person.user_id != user_id:
            raise ResourceNotFoundError(resource="Person", id=str(body.person_id))

        debt_in = DebtCreate(user_id=user_id, **body.model_dump())
        return await self.repo.create(debt_in)

    async def settle_debt(self, debt_id: UUID, user_id: UUID, amount_settled: float) -> Debt:
        debt = await self.repo.get_by_id(debt_id)
        if not debt or debt.user_id != user_id:
            raise ResourceNotFoundError(resource="Debt", id=str(debt_id))

        if amount_settled > float(debt.amount):
            raise BusinessRuleViolationError("amount_settled cannot exceed the debt amount")

        status = _derive_status(amount_settled, float(debt.amount))
        return await self.repo.update(debt, DebtUpdate(amount_settled=amount_settled, status=status))

    async def delete_debt(self, debt_id: UUID, user_id: UUID) -> None:
        debt = await self.repo.get_by_id(debt_id)
        if not debt or debt.user_id != user_id:
            raise ResourceNotFoundError(resource="Debt", id=str(debt_id))
        await self.repo.delete(debt)

    async def get_net_position(self, user_id: UUID) -> dict:
        return await self.repo.get_net_position(user_id)
