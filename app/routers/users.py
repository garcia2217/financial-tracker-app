import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_user_service
from app.models.user import User
from app.schemas.response import build_success_response
from app.schemas.user import UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    user_data = UserResponse.model_validate(current_user)
    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data={"user": user_data.model_dump(mode="json")},
            request_id=request_id,
        ),
    )


@router.post("/telegram-link")
async def generate_telegram_link(
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    code = await user_service.generate_telegram_link_code(current_user.id)

    return JSONResponse(
        status_code=200,
        content=build_success_response(
            data={"code": code},
            request_id=request_id,
        ),
    )
