from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    telegram_chat_id: Optional[int] = None
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    telegram_state: str = Field(default="AWAITING_USERNAME")

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    telegram_state: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
