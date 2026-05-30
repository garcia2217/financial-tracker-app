import secrets
import uuid
from datetime import datetime, timedelta, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
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

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# code → (jwt_token, expires_at); one-time use, 2-minute TTL
_pending_oauth_codes: dict[str, tuple[str, datetime]] = {}

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
        samesite="none" if not settings.DEBUG else "lax",
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
        samesite="none" if not settings.DEBUG else "lax",
    )
    return response


@router.get("/google/login")
async def login_google(request: Request):
    """Initiates the Google OAuth2 login flow."""
    redirect_uri = str(request.url_for('auth_google_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handles the callback from Google, exchanges token, and logs the user in."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    user_info = token.get('userinfo')
    if not user_info:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=no_user_info")

    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name")

    if not email or not google_id:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=invalid_user_info")

    service = AuthService(db)
    user = await service.login_with_google(email=email, google_id=google_id, name=name)

    app_token, _ = create_access_token(str(user.id))

    code = secrets.token_urlsafe(32)
    _pending_oauth_codes[code] = (app_token, datetime.now(timezone.utc) + timedelta(minutes=2))

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback?code={code}")


@router.post("/exchange")
async def exchange_oauth_code(code: str) -> JSONResponse:
    entry = _pending_oauth_codes.pop(code, None)

    if entry is None:
        return JSONResponse(
            status_code=400,
            content=build_error_response(
                message="Invalid or expired code",
                code=ApiErrorCode.VALIDATION_ERROR,
                request_id=str(uuid.uuid4()),
            ),
        )

    app_token, expires_at = entry
    if datetime.now(timezone.utc) > expires_at:
        return JSONResponse(
            status_code=400,
            content=build_error_response(
                message="Code expired",
                code=ApiErrorCode.VALIDATION_ERROR,
                request_id=str(uuid.uuid4()),
            ),
        )

    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response = JSONResponse(
        status_code=200,
        content=build_success_response(
            data={},
            request_id=str(uuid.uuid4()),
        ),
    )
    response.set_cookie(
        key="access_token",
        value=app_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="none" if not settings.DEBUG else "lax",
        path="/",
        max_age=max_age,
    )
    return response
