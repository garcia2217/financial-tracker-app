from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Annotated, Optional

# Balances are stored as Decimal to keep arithmetic exact; mirrors Numeric(14, 2).
Balance = Annotated[Decimal, Field(max_digits=14, decimal_places=2)]

class WalletBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WalletBody(BaseModel):
    """POST /wallets request body. user_id is injected from the JWT, not accepted from the client."""
    name: str = Field(..., min_length=1, max_length=100)
    balance: Balance = Decimal("0")

class WalletCreate(WalletBase):
    user_id: UUID
    balance: Balance = Decimal("0")

class WalletUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[Balance] = None

class WalletResponse(WalletBase):
    id: UUID
    user_id: UUID
    # Emit money as a JSON number for wire compatibility (display only, no arithmetic).
    balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
