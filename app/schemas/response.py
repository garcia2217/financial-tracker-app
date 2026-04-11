from datetime import datetime, timezone
from enum import Enum
from math import ceil
from typing import Generic, Literal, TypeVar, Any

from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiErrorCode(str, Enum):
    """Standardized error codes for frontend consumption."""

    UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    FORBIDDEN = "AUTH_FORBIDDEN"
    NOT_FOUND = "RESOURCE_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

class MetaBase(BaseModel):
    """Foundational metadata included in every response."""

    request_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MetaPagination(MetaBase):
    """Metadata specifically for paginated collections."""

    page: int
    page_size: int
    total_items: int
    total_pages: int


class Envelope(BaseModel, Generic[T]):
    """Base API envelope to ensure consistent top-level structure."""

    status: ResponseStatus
    meta: MetaBase


class SuccessResponse(Envelope[T]):
    """Standard wrapper for single-object successful responses."""

    status: Literal[ResponseStatus.SUCCESS] = ResponseStatus.SUCCESS
    data: T


class SuccessListResponse(Envelope[list[T]]):
    """Standard wrapper for paginated collection responses."""

    status: Literal[ResponseStatus.SUCCESS] = ResponseStatus.SUCCESS
    meta: MetaPagination
    data: list[T]


class ErrorDetail(BaseModel):
    """Detailed error payload."""

    message: str
    code: ApiErrorCode
    detail: dict[str, Any] | None = None


class ErrorResponse(Envelope[None]):
    """Standard wrapper for failed requests."""

    status: Literal[ResponseStatus.ERROR] = ResponseStatus.ERROR
    meta: MetaBase
    error: ErrorDetail


def create_meta(request_id: str) -> MetaBase:
    """Creates a standard metadata object."""
    return MetaBase(request_id=request_id)


def build_success_response(
    data: T, 
    request_id: str
) -> SuccessResponse[T]:
    """
    Wraps data in a standard success envelope.
    """
    return SuccessResponse(
        meta=MetaBase(request_id=request_id),
        data=data,
    ).model_dump()


def build_paginated_response(
    data: list[T],
    request_id: str,
    page: int,
    page_size: int,
    total_items: int,
) -> SuccessListResponse[T]:
    """
    Wraps a list in a paginated envelope. 
    Pagination math is handled explicitly by the caller or service layer.
    """
    total_pages = ceil(total_items / page_size) if page_size > 0 else 0
    
    return SuccessListResponse(
        meta=MetaPagination(
            request_id=request_id,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
        data=data,
    ).model_dump()
    
def build_error_response(
    message: str,
    code: ApiErrorCode,
    request_id: str,
    detail: dict[str, Any] | None = None,
) -> ErrorResponse:
    """
    Constructs a standardized error response.
    
    Args:
        message: A human-readable description of the error.
        code: A machine-readable enum string (e.g., 'AUTH_UNAUTHORIZED').
        request_id: The correlation ID (Sentry trace ID).
        detail: Optional dictionary for validation errors or extra context.
    """
    return ErrorResponse(
        meta=MetaBase(
            request_id=request_id,
        ),
        error=ErrorDetail(
            message=message,
            code=code,
            detail=detail,
        ),
    ).model_dump()