from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate

class PersonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, person_id: UUID) -> Person | None:
        result = await self.session.execute(select(Person).where(Person.id == person_id))
        return result.scalars().first()

    async def get_user_persons(self, user_id: UUID) -> Sequence[Person]:
        result = await self.session.execute(select(Person).where(Person.user_id == user_id))
        return result.scalars().all()

    async def create(self, person_in: PersonCreate) -> Person:
        db_person = Person(**person_in.model_dump(exclude_unset=True))
        self.session.add(db_person)
        await self.session.commit()
        await self.session.refresh(db_person)
        return db_person

    async def update(self, db_person: Person, person_in: PersonUpdate) -> Person:
        update_data = person_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_person, field, value)
        self.session.add(db_person)
        await self.session.commit()
        await self.session.refresh(db_person)
        return db_person
