import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import ApiErrorCode, build_error_response, build_paginated_response, build_success_response
from app.schemas.transaction import TransactionCreate, TransactionCreateRequest, TransactionResponse
from app.services.transaction import BusinessRuleViolationError, TransactionService
from app.core.exceptions import ResourceNotFoundError

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

    try:
        transaction = await service.create_transaction(transaction_in)
    except ResourceNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content=build_error_response(
                message=str(exc),
                code=ApiErrorCode.NOT_FOUND,
                request_id=request_id,
            ),
        )
    except BusinessRuleViolationError as exc:
        return JSONResponse(
            status_code=422,
            content=build_error_response(
                message=str(exc),
                code=ApiErrorCode.BUSINESS_RULE_VIOLATION,
                request_id=request_id,
            ),
        )

    return JSONResponse(
        status_code=201,
        content=build_success_response(
            data=TransactionResponse.model_validate(transaction).model_dump(mode="json"),
            request_id=request_id,
        ),
    )
