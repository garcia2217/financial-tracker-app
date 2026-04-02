from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class PersonCreate(PersonBase):
    user_id: UUID

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class PersonResponse(PersonBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
