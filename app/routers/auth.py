import uuid

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.response import ApiErrorCode, build_error_response, build_success_response
from app.schemas.user import UserResponse
from app.services.auth import AuthService, InvalidCredentialsError, create_access_token

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    service = AuthService(db)

    try:
        user = await service.login(body.username, body.password)
    except InvalidCredentialsError:
        return JSONResponse(
            status_code=401,
            content=build_error_response(
                message="Invalid username or password",
                code=ApiErrorCode.UNAUTHORIZED,
                request_id=request_id,
            ),
        )

    token, max_age = create_access_token(str(user.id))
    user_data = UserResponse.model_validate(user)

    response = JSONResponse(
        status_code=200,
        content=build_success_response(
            data={"user": user_data.model_dump(mode="json")},
            request_id=request_id,
        ),
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        path="/",
        max_age=max_age,
    )
    return response


@router.post("/logout", status_code=204)
@limiter.limit("20/minute")
async def logout(request: Request) -> Response:
    response = Response(status_code=204)
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
    )
    return response
