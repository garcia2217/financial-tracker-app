from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import FinancialOverviewRepository

class FinancialOverviewService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FinancialOverviewRepository(session)
        
    async def get_financial_overview(self, user_id: UUID, month: int, year: int):
        return await self.repo.get_financial_overview(user_id, month, year)