from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db import get_db
from app.exceptions import UnauthorizedError
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    try:
        user = await auth_service.register_user(
            db=db,
            email=data.email,
            password=data.password,
        )
        return RegisterResponse.model_validate(user)
    except ValueError as e:
        raise UnauthorizedError(str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        user = await auth_service.authenticate_user(
            db=db,
            email=data.email,
            password=data.password,
        )
        access_token = auth_service.create_token(user)
        return TokenResponse(access_token=access_token)
    except UnauthorizedError:
        raise
    except Exception:
        raise UnauthorizedError("Invalid email or password")
