from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.person import Person
from app.repositories.person import PersonRepository
from app.schemas.person import PersonCreate


class PersonService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PersonRepository(session)

    async def get_user_persons(self, user_id: UUID) -> Sequence[Person]:
        return await self.repo.get_user_persons(user_id)

    async def create_person(self, user_id: UUID, name: str) -> Person:
        person_in = PersonCreate(user_id=user_id, name=name)
        return await self.repo.create(person_in)
