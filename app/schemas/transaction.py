from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Annotated, Literal, Optional

# Money is parsed and stored as Decimal to keep balance arithmetic exact.
# Constraints mirror the Numeric(14, 2) database columns.
MoneyAmount = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]

class TransactionBase(BaseModel):
    amount: MoneyAmount
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
    amount: MoneyAmount
    type: Literal["income", "expense", "transfer"]
    description: str = Field(..., min_length=1, max_length=500)
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: datetime

class TransactionUpdate(BaseModel):
    amount: Optional[MoneyAmount] = None
    type: Optional[Literal["income", "expense", "transfer"]] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    wallet_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: Optional[datetime] = None


class TransactionUpdateRequest(BaseModel):
    """API-layer schema for PATCH /transactions/:id. All mutable fields are required (frontend sends full replacement)."""
    amount: MoneyAmount
    type: Literal["income", "expense", "transfer"]
    description: str = Field(..., min_length=1, max_length=500)
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: datetime

class TransactionMonthlySummary(BaseModel):
    totalIncome: float
    totalExpense: float


class TransactionResponse(TransactionBase):
    # Emit money as a JSON number for wire compatibility (display only, no arithmetic).
    amount: float
    id: UUID
    user_id: UUID
    wallet_id: UUID
    category_id: Optional[UUID] = None
    destination_wallet_id: Optional[UUID] = None
    transaction_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
