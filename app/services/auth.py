from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from app.core.config import settings
from app.core.exceptions import AppDomainError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class InvalidCredentialsError(AppDomainError):
    """Raised when username is not found or password does not match."""
    pass


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> tuple[str, int]:
    """Returns (encoded_jwt, max_age_seconds)."""
    expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    payload = {"sub": user_id, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expire_seconds


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def login(self, username: str, password: str) -> User:
        user = await self.repo.get_by_username(username)

        if not user or not user.password:
            raise InvalidCredentialsError("Invalid username or password")

        if not verify_password(password, user.password):
            raise InvalidCredentialsError("Invalid username or password")

        return user

    async def login_with_google(self, email: str, google_id: str, name: str | None = None) -> User:
        user = await self.repo.get_by_google_id(google_id)
        if user:
            return user
        
        user = await self.repo.get_by_email(email)
        if user:
            # Link Google ID to existing email
            return await self.repo.update(user, UserUpdate(google_id=google_id))
            
        # Create new user
        base_username = email.split("@")[0]
        username = base_username
        suffix = 1
        
        while await self.repo.get_by_username(username):
            username = f"{base_username}{suffix}"
            suffix += 1
            
        user_in = UserCreate(
            email=email,
            google_id=google_id,
            username=username,
            telegram_state="ACTIVE",
        )
        return await self.repo.create(user_in)
