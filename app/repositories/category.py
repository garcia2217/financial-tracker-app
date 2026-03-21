from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalars().first()

    async def get_user_categories(self, user_id: UUID) -> Sequence[Category]:
        result = await self.session.execute(select(Category).where(Category.user_id == user_id))
        return result.scalars().all()
        
    async def get_user_category_by_name(self, user_id: UUID, name: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.user_id == user_id, Category.name.ilike(name))
        )
        return result.scalars().first()

    async def create(self, category_in: CategoryCreate) -> Category:
        db_category = Category(**category_in.model_dump(exclude_unset=True))
        self.session.add(db_category)
        await self.session.commit()
        await self.session.refresh(db_category)
        return db_category

    async def update(self, db_category: Category, category_in: CategoryUpdate) -> Category:
        update_data = category_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        self.session.add(db_category)
        await self.session.commit()
        await self.session.refresh(db_category)
        return db_category
