import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import build_paginated_response, build_success_response
from app.schemas.transaction import TransactionCreate, TransactionCreateRequest, TransactionResponse, TransactionUpdateRequest
from app.services.transaction import TransactionService

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

PAGE_SIZE = 100


@router.get("")
async def list_transactions(
    request: Request,
    page: int = 1,
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = TransactionService(db)

    offset = (page - 1) * PAGE_SIZE
    transactions = await service.get_user_transactions(
        current_user.id, limit=PAGE_SIZE, offset=offset, year=year, month=month
    )
    total = await service.count_user_transactions(current_user.id, year=year, month=month)

    data = [TransactionResponse.model_validate(t).model_dump(mode="json") for t in transactions]

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


@router.get("/recent")
async def get_recent_transactions(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = TransactionService(db)

    transactions = await service.get_user_transactions(current_user.id, limit=limit, offset=0)
    data = [TransactionResponse.model_validate(t).model_dump(mode="json") for t in transactions]

    return JSONResponse(
        status_code=200,
        content=build_paginated_response(
            data=data,
            request_id=request_id,
            page=1,
            page_size=limit,
            total_items=len(data),
        ),
    )


@router.get("/summary")
async def get_monthly_summary(
    request: Request,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = TransactionService(db)

    summary = await service.get_monthly_summary(current_user.id, year=year, month=month)

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data=summary.model_dump(),
            request_id=request_id,
        ),
    )


@router.post("")
async def create_transaction(
    request: Request,
    body: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = TransactionService(db)

    transaction_in = TransactionCreate(
        user_id=current_user.id,
        **body.model_dump(),
    )

    transaction = await service.create_transaction(transaction_in)

    return JSONResponse(
        status_code=201,
        content=build_success_response(
            data=TransactionResponse.model_validate(transaction).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.patch("/{transaction_id}")
async def update_transaction(
    transaction_id: uuid.UUID,
    body: TransactionUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = TransactionService(db)

    transaction = await service.update_transaction(transaction_id, current_user.id, body)

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data=TransactionResponse.model_validate(transaction).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    service = TransactionService(db)

    await service.delete_transaction(transaction_id, current_user.id)

    return JSONResponse(status_code=204, content=None)
