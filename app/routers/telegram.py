from fastapi import APIRouter, Depends
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

# Simple in-memory deduplication cache to prevent Telegram timeout retries
processed_updates: set[int] = set()
MAX_CACHE_SIZE = 5000

# Telegram conversation states
STATE_AWAITING_USERNAME = "AWAITING_USERNAME"
STATE_AWAITING_PASSWORD = "AWAITING_PASSWORD"
STATE_ACTIVE = "ACTIVE"


async def _handle_new_user(
    chat_id: int,
    user_service: UserService,
    telegram_service: TelegramBotService,
) -> None:
    await user_service.create_user(UserCreate(telegram_chat_id=chat_id, telegram_state=STATE_AWAITING_USERNAME))
    await telegram_service.send_message(
        chat_id,
        "Welcome to the Financial Tracker! To get started and prepare for our future web dashboard, "
        "please reply with your desired **username**."
    )


async def _handle_awaiting_username(
    chat_id: int,
    user_id,
    text: str,
    user_service: UserService,
    telegram_service: TelegramBotService,
) -> None:
    if await user_service.get_user_by_username(text):
        await telegram_service.send_message(chat_id, "That username is already taken. Please try another one.")
        return

    await user_service.update_user(user_id, UserUpdate(username=text, telegram_state=STATE_AWAITING_PASSWORD))
    await telegram_service.send_message(
        chat_id, "Great username! Now, please reply with a secure **password** (min 8 characters)."
    )


async def _handle_awaiting_password(
    chat_id: int,
    user_id,
    text: str,
    user_service: UserService,
    category_service: CategoryService,
    wallet_service: WalletService,
    telegram_service: TelegramBotService,
) -> None:
    if len(text) < 8:
        await telegram_service.send_message(chat_id, "Password must be at least 8 charac_ters. Please try again.")
        return

    await user_service.update_user(user_id, UserUpdate(password=text, telegram_state=STATE_ACTIVE))
    await category_service.seed_default_categories(user_id)
    await wallet_service.create_wallet(WalletCreate(user_id=user_id, name="Cash", balance=0.0))
    await telegram_service.send_message(
        chat_id,
        "Registration complete! 🎉 You can now start logging your finances. Try sending something like 'Makan bakso 50k'."
    )


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
    parsed_data = await gemini_service.parse_transaction_text(text)

    if "error" in parsed_data:
        await telegram_service.send_message(chat_id, f"Oops: {parsed_data['error']}")
        return

    amount = parsed_data.get("amount")
    txn_type = parsed_data.get("type", "expense")
    cat_name = parsed_data.get("category", "Other")
    desc = parsed_data.get("description", "No description provided")

    category = await category_service.get_or_create_by_name(user_id, cat_name, txn_type)

    user_wallets = await wallet_service.get_user_wallets(user_id)
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


@router.post("/webhook")
async def telegram_webhook(
    payload: TelegramWebhook,
    user_service: UserService = Depends(get_user_service),
    category_service: CategoryService = Depends(get_category_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    telegram_service: TelegramBotService = Depends(get_telegram_service),
):
    if payload.update_id in processed_updates:
        return {"status": "already_processed"}

    processed_updates.add(payload.update_id)
    if len(processed_updates) > MAX_CACHE_SIZE:
        processed_updates.clear()

    if not payload.message or not payload.message.text:
        return {"status": "ignored"}

    chat_id = payload.message.chat.id
    text = payload.message.text.strip()
    user = await user_service.get_user_by_telegram_id(chat_id)

    if not user:
        await _handle_new_user(chat_id, user_service, telegram_service)
    elif user.telegram_state == STATE_AWAITING_USERNAME:
        await _handle_awaiting_username(chat_id, user.id, text, user_service, telegram_service)
    elif user.telegram_state == STATE_AWAITING_PASSWORD:
        await _handle_awaiting_password(chat_id, user.id, text, user_service, category_service, wallet_service, telegram_service)
    else:
        await _handle_transaction(chat_id, user.id, text, gemini_service, category_service, wallet_service, transaction_service, telegram_service)

    return {"status": "ok"}