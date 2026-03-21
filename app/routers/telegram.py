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

# Import from the shared dependencies layer
from app.dependencies.services import (
    get_user_service,
    get_category_service,
    get_wallet_service,
    get_transaction_service,
    get_gemini_service,
    get_telegram_service
)

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])

# Simple in-memory cache to prevent Telegram timeout retries from causing duplicate actions
processed_updates = set()

@router.post("/webhook")
async def telegram_webhook(
    payload: TelegramWebhook,
    user_service: UserService = Depends(get_user_service),
    category_service: CategoryService = Depends(get_category_service),
    wallet_service: WalletService = Depends(get_wallet_service),
    transaction_service: TransactionService = Depends(get_transaction_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    telegram_service: TelegramBotService = Depends(get_telegram_service)
):
    # Ignore Telegram's aggressive retries by checking the update_id
    if payload.update_id in processed_updates:
        return {"status": "already_processed"}
        
    processed_updates.add(payload.update_id)
    if len(processed_updates) > 5000:
        processed_updates.clear() # Prevent memory leak and reset
        
    # Ignore generic actions that aren't messages
    if not payload.message or not payload.message.text:
        return {"status": "ignored"}
        
    chat_id = payload.message.chat.id
    text = payload.message.text.strip()
    
    # 1. State Machine: Determine User Profile Context
    user = await user_service.get_user_by_telegram_id(chat_id)
    
    # First time they've ever spoken to the bot
    if not user:
        new_user = UserCreate(telegram_chat_id=chat_id, telegram_state="AWAITING_USERNAME")
        user = await user_service.create_user(new_user)
        await telegram_service.send_message(
            chat_id, 
            "Welcome to the Financial Tracker! To get started and prepare for our future web dashboard, please reply with your desired **username**."
        )
        return {"status": "ok"}
        
    # Waiting on their chosen Username
    if user.telegram_state == "AWAITING_USERNAME":
        existing = await user_service.get_user_by_username(text)
        if existing:
            await telegram_service.send_message(chat_id, "That username is already taken. Please try another one.")
            return {"status": "ok"}
            
        await user_service.update_user(user.id, UserUpdate(username=text, telegram_state="AWAITING_PASSWORD"))
        await telegram_service.send_message(chat_id, "Great username! Now, please reply with a secure **password** (min 8 characters).")
        return {"status": "ok"}
        
    # Waiting on their chosen Password
    elif user.telegram_state == "AWAITING_PASSWORD":
        if len(text) < 8:
            await telegram_service.send_message(chat_id, "Password must be at least 8 characters. Please try again.")
            return {"status": "ok"}
            
        await user_service.update_user(user.id, UserUpdate(password=text, telegram_state="ACTIVE"))
        
        # Hydrate default data context
        await category_service.seed_default_categories(user.id)
        await wallet_service.create_wallet(WalletCreate(user_id=user.id, name="Cash", balance=0.0))
        
        await telegram_service.send_message(
            chat_id, 
            "Registration complete! 🎉 You can now start logging your finances. Try sending something like 'Makan bakso 50k'."
        )
        return {"status": "ok"}
        
    # 2. Extract Data using NLP Gemini Pipeline
    parsed_data = await gemini_service.parse_transaction_text(text)
    
    if "error" in parsed_data:
        err_msg = parsed_data["error"]
        await telegram_service.send_message(chat_id, f"Oops: {err_msg}")
        return {"status": "ok"}
        
    # 3. Handle Business Workflow (Transactions)
    amount = parsed_data.get("amount")
    txn_type = parsed_data.get("type", "expense")
    cat_name = parsed_data.get("category", "Other")
    desc = parsed_data.get("description", "No description provided")
    
    category = await category_service.get_or_create_by_name(user.id, cat_name, txn_type)
    
    # Simple default to their oldest active wallet mapping if no explicit wallet specified
    user_wallets = await wallet_service.get_user_wallets(user.id)
    if not user_wallets:
        wallet = await wallet_service.create_wallet(WalletCreate(user_id=user.id, name="Cash", balance=0.0))
    else:
        wallet = user_wallets[0]
        
    txn_create = TransactionCreate(
        user_id=user.id,
        wallet_id=wallet.id,
        category_id=category.id, # type: ignore
        amount=amount, # type: ignore
        type=txn_type, # type: ignore
        description=desc,
        transaction_date=None
    )
    
    try:
        await transaction_service.create_transaction(txn_create)
        updated_wallet = await wallet_service.get_wallet(wallet.id)
        
        reply = f"✅ Recorded: {txn_type.title()} of Rp {amount} for {category.name} ({desc}).\nNew {wallet.name} balance: Rp {updated_wallet.balance:,.0f}"
        await telegram_service.send_message(chat_id, reply)
    except Exception as e:
        await telegram_service.send_message(chat_id, f"Failed to record transaction: {str(e)}")
        
    return {"status": "ok"}
