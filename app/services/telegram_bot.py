import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramBotService:
    def __init__(self):
        self.bot_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(self, chat_id: int, text: str):
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.bot_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text}
                )
            except Exception:
                logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)
