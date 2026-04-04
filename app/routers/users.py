from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.schemas import PaginatedResponse, PaginationParams, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> PaginatedResponse[UserResponse]:
    users, total = await user_service.list_users(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    return PaginatedResponse.create(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> UserResponse:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        from app.exceptions import UserNotFoundError

        raise UserNotFoundError()
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> UserResponse:
    update_data = data.model_dump(exclude_unset=True)
    user = await user_service.update_user(db, user_id, update_data)
    return UserResponse.model_validate(user)
