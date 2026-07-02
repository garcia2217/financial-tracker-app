import logging
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    AppDomainError,
    BusinessRuleViolationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from app.routers import (
    auth_router,
    budgets_router,
    categories_router,
    debts_router,
    financial_overview_router,
    persons_router,
    telegram_router,
    transactions_router,
    users_router,
    wallets_router,
)
from app.schemas.response import ApiErrorCode, build_error_response

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).warning(
        "Starting up | ENVIRONMENT=%s DEBUG=%s FRONTEND_URL=%s",
        settings.ENVIRONMENT,
        settings.DEBUG,
        settings.FRONTEND_URL,
    )
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.error("Failed to connect to the database: %s", e)
        raise e

    yield

    await engine.dispose()
    logger.info("Database connection closed.")


app = FastAPI(
    title="Financial Tracker App",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    https_only=not settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=build_error_response(
            message="Validation error",
            code=ApiErrorCode.VALIDATION_ERROR,
            request_id=str(uuid.uuid4()),
            detail={"errors": exc.errors()},
        ),
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=404,
        content=build_error_response(
            message=f"That {exc.resource.lower()} could not be found.",
            code=ApiErrorCode.NOT_FOUND,
            request_id=str(uuid.uuid4()),
        ),
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(
        status_code=403,
        content=build_error_response(
            message=str(exc),
            code=ApiErrorCode.FORBIDDEN,
            request_id=str(uuid.uuid4()),
        ),
    )


@app.exception_handler(BusinessRuleViolationError)
async def business_rule_violation_handler(request: Request, exc: BusinessRuleViolationError):
    return JSONResponse(
        status_code=422,
        content=build_error_response(
            message=str(exc),
            code=ApiErrorCode.BUSINESS_RULE_VIOLATION,
            request_id=str(uuid.uuid4()),
        ),
    )


@app.exception_handler(AppDomainError)
async def app_domain_error_handler(request: Request, exc: AppDomainError):
    return JSONResponse(
        status_code=400,
        content=build_error_response(
            message=str(exc),
            code=ApiErrorCode.VALIDATION_ERROR,
            request_id=str(uuid.uuid4()),
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    logger.error("Unhandled exception [%s] on %s:\n%s", request_id, request.url.path, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            message="An unexpected error occurred.",
            code=ApiErrorCode.INTERNAL_ERROR,
            request_id=request_id,
        ),
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(wallets_router)
app.include_router(categories_router)
app.include_router(budgets_router)
app.include_router(persons_router)
app.include_router(debts_router)
app.include_router(telegram_router)
app.include_router(financial_overview_router)
