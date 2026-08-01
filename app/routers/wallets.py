import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import build_paginated_response, build_success_response
from app.schemas.wallet import WalletBody, WalletCreate, WalletResponse, WalletUpdate
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


@router.post("")
async def create_wallet(
    body: WalletBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = WalletService(db)

    wallet_in = WalletCreate(user_id=current_user.id, name=body.name, balance=body.balance)
    wallet = await service.create_wallet(wallet_in)
    data = WalletResponse.model_validate(wallet).model_dump(mode="json")

    return JSONResponse(
        status_code=201,
        content=build_success_response(data=data, request_id=request_id),
    )


@router.patch("/{wallet_id}")
async def update_wallet(
    wallet_id: uuid.UUID,
    body: WalletUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = WalletService(db)

    wallet = await service.update_wallet(wallet_id, current_user.id, body)
    data = WalletResponse.model_validate(wallet).model_dump(mode="json")

    return JSONResponse(
        status_code=200,
        content=build_success_response(data=data, request_id=request_id),
    )


@router.patch("/{wallet_id}/default")
async def set_default_wallet(
    wallet_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = WalletService(db)

    wallet = await service.set_default_wallet(wallet_id, current_user.id)
    data = WalletResponse.model_validate(wallet).model_dump(mode="json")

    return JSONResponse(
        status_code=200,
        content=build_success_response(data=data, request_id=request_id),
    )


@router.delete("/{wallet_id}")
async def delete_wallet(
    wallet_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = WalletService(db)
    await service.delete_wallet(wallet_id, current_user.id)
    return Response(status_code=204)
