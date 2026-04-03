from pydantic import BaseModel
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from typing import List

class TransactionOverview(BaseModel):
    category_name: str
    type: str
    amount: Decimal
    transaction_date: datetime
    description: str

class FinancialOverview(BaseModel):
    transactions: List[TransactionOverview]
    total_assets: Decimal
    total_liabilities: Decimal
    monthly_income: Decimal
    monthly_expense: Decimal
    savings_rate: float