from pydantic import BaseModel
from typing import Optional

class TelegramChat(BaseModel):
    id: int

class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: Optional[str] = None

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
