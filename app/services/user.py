from uuid import UUID
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
