from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, AppDomainError
from app.repositories import TransactionRepository
from app.schemas import TransactionCreate, WalletUpdate
from app.services.wallet import WalletService

class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TransactionRepository(session)
        self.wallet_service = WalletService(session)
        
    async def get_transaction(self, transaction_id: UUID):
        txn = await self.repo.get_by_id(transaction_id)
        if not txn:
            raise ResourceNotFoundError(resource="Transaction", id=str(transaction_id))
        return txn

    async def get_user_transactions(self, user_id: UUID, limit: int = 50, offset: int = 0):
        return await self.repo.get_user_transactions(user_id, limit, offset)

    async def create_transaction(self, transaction_in: TransactionCreate):
        # 1. Fetch wallet to ensure it exists
        wallet = await self.wallet_service.get_wallet(transaction_in.wallet_id)
        
        # 2. Adjust balance based on math logic
        new_balance = float(wallet.balance)
        if transaction_in.type == "expense":
            new_balance -= transaction_in.amount
        elif transaction_in.type == "income":
            new_balance += transaction_in.amount
        elif transaction_in.type == "transfer":
            if not transaction_in.destination_wallet_id:
                raise AppDomainError("Transfers require a destination_wallet_id")
            new_balance -= transaction_in.amount
            
            # 3. Add to destination wallet
            dest_wallet = await self.wallet_service.get_wallet(transaction_in.destination_wallet_id)
            dest_new_balance = float(dest_wallet.balance) + transaction_in.amount
            await self.wallet_service.update_wallet(dest_wallet.id, WalletUpdate(balance=dest_new_balance))
        else:
            raise AppDomainError(f"Invalid transaction type: {transaction_in.type}")

        # Update primary wallet
        await self.wallet_service.update_wallet(wallet.id, WalletUpdate(balance=new_balance))

        # Create the transaction record
        return await self.repo.create(transaction_in)
