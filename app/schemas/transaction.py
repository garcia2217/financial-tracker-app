from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional

class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    type: Literal["income", "expense", "transfer"]
    description: str = Field(..., min_length=1, max_length=500)
    transaction_date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    user_id: UUID
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None


class TransactionCreateRequest(BaseModel):
    """API-layer schema for POST /transactions. user_id is injected from the JWT, not sent by the client."""
    amount: float = Field(..., gt=0)
    type: Literal["income", "expense", "transfer"]
    description: str = Field(..., min_length=1, max_length=500)
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: datetime

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[Literal["income", "expense", "transfer"]] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    wallet_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: Optional[datetime] = None

class TransactionMonthlySummary(BaseModel):
    totalIncome: float
    totalExpense: float


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
