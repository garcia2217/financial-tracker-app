from uuid import UUID
from datetime import datetime, timedelta, timezone
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from app.core.exceptions import ResourceNotFoundError
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def get_user(self, user_id: UUID):
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(resource="User", id=str(user_id))
        return user

    async def get_user_by_telegram_id(self, telegram_chat_id: int):
        return await self.repo.get_by_telegram_id(telegram_chat_id)

    async def get_user_by_username(self, username: str):
        return await self.repo.get_by_username(username)

    async def create_user(self, user_in: UserCreate):
        if user_in.password:
            user_in.password = hash_password(user_in.password[:72])
        return await self.repo.create(user_in)

    async def update_user(self, user_id: UUID, user_in: UserUpdate):
        user = await self.get_user(user_id)
        if user_in.password:
            user_in.password = hash_password(user_in.password[:72])
        return await self.repo.update(user, user_in)

    async def generate_telegram_link_code(self, user_id: UUID) -> str:
        # Generate 6 digit code
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        await self.update_user(user_id, UserUpdate(
            telegram_link_code=code,
            telegram_link_expires_at=expires_at
        ))
        return code

    async def link_telegram_account(self, code: str, chat_id: int) -> bool:
        user = await self.repo.get_by_telegram_link_code(code)
        if not user:
            return False
            
        # Make datetime aware for comparison if it's naive
        expires_at = user.telegram_link_expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if not expires_at or expires_at < datetime.now(timezone.utc):
            return False
            
        # Update user
        await self.update_user(user.id, UserUpdate(
            telegram_chat_id=chat_id,
            telegram_state="ACTIVE",
            telegram_link_code=None,
            telegram_link_expires_at=None
        ))
        return True
