import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreateRequest, BudgetPatchRequest, BudgetResponse
from app.schemas.response import ApiErrorCode, build_error_response, build_paginated_response, build_success_response
from app.services.budget import BudgetService, BusinessRuleViolationError

router = APIRouter(prefix="/api/v1/budgets", tags=["budgets"])

PAGE_SIZE = 100


@router.get("/effective")
async def get_effective_budgets(
    request: Request,
    year: int,
    month: int,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = BudgetService(db)

    budgets = await service.get_effective_budgets(current_user.id, year=year, month=month)
    total = len(budgets)
    offset = (page - 1) * PAGE_SIZE
    page_budgets = budgets[offset : offset + PAGE_SIZE]

    data = [BudgetResponse.model_validate(b).model_dump(mode="json") for b in page_budgets]

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
async def create_budget(
    request: Request,
    body: BudgetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = BudgetService(db)

    try:
        budget = await service.create_budget(current_user.id, body)
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
            data=BudgetResponse.model_validate(budget).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.patch("/{budget_id}")
async def update_budget(
    request: Request,
    budget_id: UUID,
    body: BudgetPatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = BudgetService(db)

    try:
        budget = await service.update_budget(budget_id, current_user.id, body.amount)
    except ResourceNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content=build_error_response(
                message=str(exc),
                code=ApiErrorCode.NOT_FOUND,
                request_id=request_id,
            ),
        )

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data=BudgetResponse.model_validate(budget).model_dump(mode="json"),
            request_id=request_id,
        ),
    )


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    request: Request,
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    request_id = str(uuid.uuid4())
    service = BudgetService(db)

    try:
        await service.delete_budget(budget_id, current_user.id)
    except ResourceNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content=build_error_response(
                message=str(exc),
                code=ApiErrorCode.NOT_FOUND,
                request_id=request_id,
            ),
        )

    return Response(status_code=204)
