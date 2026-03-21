from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CategoryRepository(session)

    async def get_category(self, category_id: UUID):
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise ResourceNotFoundError(resource="Category", id=str(category_id))
        return category

    async def get_user_categories(self, user_id: UUID):
        return await self.repo.get_user_categories(user_id)

    async def get_or_create_by_name(self, user_id: UUID, name: str, cat_type: str = "expense"):
        category = await self.repo.get_user_category_by_name(user_id, name)
        if not category:
            new_cat = CategoryCreate(user_id=user_id, name=name, type=cat_type) # type: ignore
            category = await self.repo.create(new_cat)
        return category

    async def create_category(self, category_in: CategoryCreate):
        return await self.repo.create(category_in)

    async def update_category(self, category_id: UUID, category_in: CategoryUpdate):
        category = await self.get_category(category_id)
        return await self.repo.update(category, category_in)
        
    async def seed_default_categories(self, user_id: UUID):
        defaults = [
            CategoryCreate(user_id=user_id, name="Food", type="expense"),
            CategoryCreate(user_id=user_id, name="Transport", type="expense"),
            CategoryCreate(user_id=user_id, name="Salary", type="income"),
            CategoryCreate(user_id=user_id, name="Other", type="expense"),
        ]
        for cat in defaults:
            await self.repo.create(cat)
