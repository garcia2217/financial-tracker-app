from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import NullPool

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_maker() as session:
        yield session
