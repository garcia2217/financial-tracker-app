from uuid import UUID
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.debt import Debt
from app.schemas.debt import DebtCreate, DebtUpdate

class DebtRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, debt_id: UUID) -> Debt | None:
        result = await self.session.execute(select(Debt).where(Debt.id == debt_id))
        return result.scalars().first()

    async def get_user_debts(self, user_id: UUID) -> Sequence[Debt]:
        result = await self.session.execute(
            select(Debt).where(Debt.user_id == user_id).order_by(Debt.created_at.desc())
        )
        return result.scalars().all()

    async def get_net_position(self, user_id: UUID) -> dict:
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(Debt.type == "receivable", Debt.status != "settled"),
                            Debt.amount - Debt.amount_settled,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("totalReceivable"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(Debt.type == "payable", Debt.status != "settled"),
                            Debt.amount - Debt.amount_settled,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("totalPayable"),
        ).where(Debt.user_id == user_id)

        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "totalReceivable": float(row.totalReceivable),
            "totalPayable": float(row.totalPayable),
        }

    async def create(self, debt_in: DebtCreate) -> Debt:
        db_debt = Debt(**debt_in.model_dump(exclude_unset=True))
        self.session.add(db_debt)
        await self.session.commit()
        await self.session.refresh(db_debt)
        return db_debt

    async def update(self, db_debt: Debt, debt_in: DebtUpdate) -> Debt:
        update_data = debt_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_debt, field, value)
        self.session.add(db_debt)
        await self.session.commit()
        await self.session.refresh(db_debt)
        return db_debt

    async def delete(self, db_debt: Debt) -> None:
        await self.session.delete(db_debt)
        await self.session.commit()
