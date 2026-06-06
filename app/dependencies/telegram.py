import hmac
import logging

from fastapi import Header, HTTPException, status

from app.core.config import settings
from app.schemas.response import ApiErrorCode

logger = logging.getLogger(__name__)

# Telegram sends this header on every webhook request when a secret_token was
# registered via setWebhook. See https://core.telegram.org/bots/api#setwebhook
_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


async def verify_telegram_secret(
    secret_token: str | None = Header(default=None, alias=_SECRET_HEADER),
) -> None:
    """Reject any webhook call whose secret token does not match the configured one.

    Fails closed: if no secret is configured the endpoint rejects every request,
    so the webhook can never run unauthenticated.
    """
    forbidden = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Invalid Telegram webhook secret",
            "code": ApiErrorCode.FORBIDDEN,
        },
    )

    if not settings.TELEGRAM_WEBHOOK_SECRET:
        logger.error(
            "TELEGRAM_WEBHOOK_SECRET is not configured; rejecting webhook request."
        )
        raise forbidden

    if secret_token is None or not hmac.compare_digest(
        secret_token, settings.TELEGRAM_WEBHOOK_SECRET
    ):
        logger.warning("Rejected Telegram webhook with missing/invalid secret token.")
        raise forbidden
