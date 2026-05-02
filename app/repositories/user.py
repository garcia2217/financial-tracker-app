from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
        
    async def get_by_telegram_id(self, telegram_chat_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_chat_id == telegram_chat_id))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.google_id == google_id))
        return result.scalars().first()

    async def get_by_telegram_link_code(self, code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_link_code == code))
        return result.scalars().first()

    async def create(self, user_in: UserCreate) -> User:
        db_user = User(**user_in.model_dump(exclude_unset=True))
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def update(self, db_user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
