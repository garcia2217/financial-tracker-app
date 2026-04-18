from .auth import router as auth_router
from .categories import router as categories_router
from .financial_overview import router as financial_overview_router
from .telegram import router as telegram_router
from .transactions import router as transactions_router
from .users import router as users_router
from .wallets import router as wallets_router

__all__ = [
    "auth_router",
    "categories_router",
    "financial_overview_router",
    "telegram_router",
    "transactions_router",
    "users_router",
    "wallets_router",
]
