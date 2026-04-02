from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional

class DebtBase(BaseModel):
    person_id: UUID
    amount: float = Field(..., gt=0)
    type: Literal["receivable", "payable"]
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None

class DebtCreate(DebtBase):
    user_id: UUID

class DebtUpdate(BaseModel):
    amount_settled: Optional[float] = Field(None, ge=0)
    status: Optional[Literal["pending", "partial", "settled"]] = None
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None

class DebtResponse(DebtBase):
    id: UUID
    user_id: UUID
    amount_settled: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
