from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class WalletBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WalletBody(BaseModel):
    """POST /wallets request body. user_id is injected from the JWT, not accepted from the client."""
    name: str = Field(..., min_length=1, max_length=100)
    balance: float = Field(default=0.0)

class WalletCreate(WalletBase):
    user_id: UUID
    balance: float = Field(default=0.0)

class WalletUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[float] = None

class WalletResponse(WalletBase):
    id: UUID
    user_id: UUID
    balance: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
