from collections import deque

from fastapi import APIRouter, Depends
from app.dependencies.telegram import verify_telegram_secret
from app.schemas.telegram import TelegramWebhook
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.wallet import WalletCreate
from app.schemas.transaction import TransactionCreate

from app.services.user import UserService
from app.services.category import CategoryService
from app.services.wallet import WalletService
from app.services.transaction import TransactionService
from app.services.gemini import GeminiService
from app.services.telegram_bot import TelegramBotService

from app.dependencies.services import (
    get_user_service,
    get_category_service,
    get_wallet_service,
    get_transaction_service,
    get_gemini_service,
    get_telegram_service
)

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])

# In-process deduplication to absorb Telegram retry storms.
# NOTE: This is process-local — duplicate delivery across workers is still possible
# in a multi-worker deployment. Use a shared store (Redis/DB) if you scale beyond
# a single worker.
MAX_CACHE_SIZE = 1000
_processed_ids: set[int] = set()
_processed_order: deque[int] = deque()

# Telegram conversation states
STATE_AWAITING_USERNAME = "AWAITING_USERNAME"
STATE_AWAITING_PASSWORD = "AWAITING_PASSWORD"
STATE_ACTIVE = "ACTIVE"


# Removed old auth handlers


async def _handle_transaction(
    chat_id: int,
    user_id,
    text: str,
    gemini_service: GeminiService,
    category_service: CategoryService,
    wallet_service: WalletService,
    transaction_service: TransactionService,
    telegram_service: TelegramBotService,
) -> None:
    user_wallets = await wallet_service.get_user_wallets(user_id)
    parsed_data = await gemini_service.parse_transaction_text(
        text, [wallet.name for wallet in user_wallets]
    )

    if "error" in parsed_data:
        await telegram_service.send_message(chat_id, f"Oops: {parsed_data['error']}")
        return

    amount = parsed_data.get("amount")
    txn_type = parsed_data.get("type", "expense")
    cat_name = parsed_data.get("category", "Other")
    desc = parsed_data.get("description", "No description provided")

    category = await category_service.get_or_create_by_name(user_id, cat_name, txn_type)

    wallet = user_wallets[0] if user_wallets else await wallet_service.create_wallet(
        WalletCreate(user_id=user_id, name="Cash", balance=0.0)
    )

    txn_create = TransactionCreate(
        user_id=user_id,
        wallet_id=wallet.id,
        category_id=category.id,  # type: ignore
        amount=amount,  # type: ignore
        type=txn_type,  # type: ignore
        description=desc,
        transaction_date=None,
    )

    try:
        await transaction_service.create_transaction(txn_create)
        updated_wallet = await wallet_service.get_wallet(wallet.id)
        reply = (
            f"✅ Recorded: {txn_type.title()} of Rp {amount:,} for {category.name} ({desc}).\n"
            f"New {wallet.name} balance: Rp {updated_wallet.balance:,.0f}"
        )
        await telegram_service.send_message(chat_id, reply)
    except Exception as e:
        await telegram_service.send_message(chat_id, f"Failed to record transaction: {str(e)}")


@router.post("/webhook", dependencies=[Depends(verify_telegram_secret)])
async def telegram_webhook(
    payload: TelegramWebhook,
    user_service: UserService = Depends(get_user_service),
    category_service: CategoryService = Depends(get_category_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    telegram_service: TelegramBotService = Depends(get_telegram_service),
):
    if payload.update_id in _processed_ids:
        return {"status": "already_processed"}

    if len(_processed_ids) >= MAX_CACHE_SIZE:
        oldest = _processed_order.popleft()
        _processed_ids.discard(oldest)
    _processed_ids.add(payload.update_id)
    _processed_order.append(payload.update_id)

    if not payload.message or not payload.message.text:
        return {"status": "ignored"}

    chat_id = payload.message.chat.id
    text = payload.message.text.strip()
    user = await user_service.get_user_by_telegram_id(chat_id)

    if not user:
        if text.startswith("/link "):
            code = text.split(" ", 1)[1].strip()
            success = await user_service.link_telegram_account(code, chat_id)
            if success:
                await telegram_service.send_message(chat_id, "✅ Account linked successfully! You can now log your finances here.")
            else:
                await telegram_service.send_message(chat_id, "❌ Invalid or expired linking code. Please generate a new one from the web dashboard.")
        else:
            await telegram_service.send_message(
                chat_id, 
                "Welcome! I don't recognize this account. Please log in to the web dashboard, click 'Connect Telegram', and send me the linking code provided (e.g., /link 123456)."
            )
    else:
        await _handle_transaction(chat_id, user.id, text, gemini_service, category_service, wallet_service, transaction_service, telegram_service)

    return {"status": "ok"}