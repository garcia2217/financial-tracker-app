import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.category import CategoryBody, CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.response import build_paginated_response, build_success_response
from app.services.category import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

PAGE_SIZE = 100


@router.get("")
async def list_categories(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = CategoryService(db)

    categories = await service.get_user_categories(current_user.id)
    total = len(categories)
    offset = (page - 1) * PAGE_SIZE
    page_categories = categories[offset : offset + PAGE_SIZE]

    data = [CategoryResponse.model_validate(c).model_dump(mode="json") for c in page_categories]

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
async def create_category(
    body: CategoryBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = CategoryService(db)

    category_in = CategoryCreate(user_id=current_user.id, name=body.name, type=body.type)
    category = await service.create_category(category_in)
    data = CategoryResponse.model_validate(category).model_dump(mode="json")

    return JSONResponse(
        status_code=201,
        content=build_success_response(data=data, request_id=request_id),
    )


@router.patch("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = CategoryService(db)

    category = await service.update_category(category_id, current_user.id, body)
    data = CategoryResponse.model_validate(category).model_dump(mode="json")

    return JSONResponse(
        status_code=200,
        content=build_success_response(data=data, request_id=request_id),
    )


@router.delete("/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = CategoryService(db)
    await service.delete_category(category_id, current_user.id)
    return Response(status_code=204)
