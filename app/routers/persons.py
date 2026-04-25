import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.person import PersonBase, PersonResponse
from app.schemas.response import ApiErrorCode, build_error_response, build_paginated_response, build_success_response
from app.services.person import PersonService

router = APIRouter(prefix="/api/v1/persons", tags=["persons"])

PAGE_SIZE = 100


@router.get("")
async def list_persons(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = PersonService(db)

    persons = await service.get_user_persons(current_user.id)
    total = len(persons)
    offset = (page - 1) * PAGE_SIZE
    page_persons = persons[offset : offset + PAGE_SIZE]

    data = [PersonResponse.model_validate(p).model_dump(mode="json") for p in page_persons]

    return JSONResponse(
        status_code=200,
        content=build_paginated_response(
            data=data,
            request_id=request_id,
            page=page,
            page_size=PAGE_SIZE,
            total_items=total,
        ),
    )


@router.post("")
async def create_person(
    request: Request,
    body: PersonBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = PersonService(db)

    person = await service.create_person(current_user.id, body.name)

    return JSONResponse(
        status_code=201,
        content=build_success_response(
            data=PersonResponse.model_validate(person).model_dump(mode="json"),
            request_id=request_id,
        ),
    )
