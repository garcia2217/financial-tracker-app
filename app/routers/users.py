import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import build_success_response
from app.schemas.user import UserResponse

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
