import httpx
from app.core.config import settings

class TelegramBotService:
    def __init__(self):
        self.bot_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(self, chat_id: int, text: str):
        """
        Sends a text message back to the specified Telegram chat ID.
        In a production setting, retries or error tracking would be logged here.
        """
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.bot_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text}
                )
            except Exception as e:
                # Typically we would log this safely, pass for MVP
                pass
