from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class BudgetBase(BaseModel):
    category_id: UUID
    amount: float = Field(..., gt=0)
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = None
    is_default: bool = False


class BudgetCreate(BudgetBase):
    user_id: UUID


class BudgetUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = None
    is_default: Optional[bool] = None


class BudgetCreateRequest(BaseModel):
    """API-layer schema for POST /budgets. user_id is injected from the JWT."""
    category_id: UUID
    amount: float = Field(..., gt=0)
    is_default: bool
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = None


class BudgetPatchRequest(BaseModel):
    """API-layer schema for PATCH /budgets/{id}. Only amount is editable."""
    amount: float = Field(..., gt=0)


class BudgetResponse(BudgetBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
