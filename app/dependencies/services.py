from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.financial_overview import FinancialOverviewService
from app.services.gemini import GeminiService
from app.services.telegram_bot import TelegramBotService
from app.services.transaction import TransactionService
from app.services.user import UserService
from app.services.wallet import WalletService


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

def get_wallet_service(db: AsyncSession = Depends(get_db)) -> WalletService:
    return WalletService(db)

def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(db)

def get_transaction_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    return TransactionService(db)

def get_gemini_service() -> GeminiService:
    return GeminiService()

def get_telegram_service() -> TelegramBotService:
    return TelegramBotService()

def get_financial_overview_service(db: AsyncSession = Depends(get_db)) -> FinancialOverviewService:
    return FinancialOverviewService(db)