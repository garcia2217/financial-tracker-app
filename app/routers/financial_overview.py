from datetime import datetime
from fastapi import APIRouter, Depends

from app.services.financial_overview import FinancialOverviewService

from app.dependencies.services import (
    get_financial_overview_service
)

router = APIRouter(prefix="/api/v1/financial-overview", tags=["financial overview"])

@router.get("")
async def financial_overview(
    financial_overview_service: FinancialOverviewService = Depends(get_financial_overview_service),
):
    return await financial_overview_service.get_financial_overview(
        user_id="7153d1af-4f01-4a9a-8277-2591745baa02",
        month=datetime.now().month,
        year=datetime.now().year
    )
