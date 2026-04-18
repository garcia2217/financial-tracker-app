import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import build_paginated_response
from app.schemas.wallet import WalletResponse
from app.services.wallet import WalletService

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])

PAGE_SIZE = 100


@router.get("")
async def list_wallets(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = WalletService(db)

    wallets = await service.get_user_wallets(current_user.id)
    total = len(wallets)
    offset = (page - 1) * PAGE_SIZE
    page_wallets = wallets[offset : offset + PAGE_SIZE]

    data = [WalletResponse.model_validate(w).model_dump(mode="json") for w in page_wallets]

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
