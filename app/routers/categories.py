import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.category import CategoryResponse
from app.schemas.response import build_paginated_response
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
