import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.debt import DebtCreateRequest, DebtResponse, DebtSettleRequest
from app.schemas.response import build_paginated_response, build_success_response
from app.services.debt import DebtService

router = APIRouter(prefix="/api/v1/debts", tags=["debts"])

PAGE_SIZE = 100


@router.get("/net-position")
async def get_net_position(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = DebtService(db)

    net_position = await service.get_net_position(current_user.id)

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data=net_position,
            request_id=request_id,
        ),
    )


@router.get("")
async def list_debts(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = DebtService(db)

    debts = await service.get_user_debts(current_user.id)
    total = len(debts)
    offset = (page - 1) * PAGE_SIZE
    page_debts = debts[offset : offset + PAGE_SIZE]

    data = [DebtResponse.model_validate(d).model_dump(mode="json") for d in page_debts]

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
async def create_debt(
    request: Request,
    body: DebtCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = DebtService(db)

    debt = await service.create_debt(current_user.id, body)

    return JSONResponse(
        status_code=201,
        content=build_success_response(
            data=DebtResponse.model_validate(debt).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.patch("/{debt_id}")
async def settle_debt(
    request: Request,
    debt_id: UUID,
    body: DebtSettleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = DebtService(db)

    debt = await service.settle_debt(debt_id, current_user.id, body.amount_settled)

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data=DebtResponse.model_validate(debt).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.delete("/{debt_id}", status_code=204)
async def delete_debt(
    request: Request,
    debt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = DebtService(db)

    await service.delete_debt(debt_id, current_user.id)

    return Response(status_code=204)
