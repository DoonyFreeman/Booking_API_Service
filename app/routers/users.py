from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.limiter import limiter, users_limit
from app.schemas import PaginatedResponse, PaginationParams, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить профиль текущего пользователя",
    description="Возвращает данные авторизованного пользователя. Требует JWT токен.",
)
@limiter.limit(users_limit)
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="Список пользователей",
    description="Возвращает список всех пользователей с пагинацией. Требует права администратора.",
)
@limiter.limit(users_limit)
async def list_users(
    request: Request,
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


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя по ID",
    description="Возвращает данные пользователя по его идентификатору. Требует права администратора.",
)
@limiter.limit(users_limit)
async def get_user(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> UserResponse:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        from app.exceptions import UserNotFoundError

        raise UserNotFoundError()
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Обновить пользователя",
    description="Обновляет данные пользователя по его ID (email, role, is_active). Требует права администратора.",
)
@limiter.limit(users_limit)
async def update_user(
    request: Request,
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> UserResponse:
    update_data = data.model_dump(exclude_unset=True)
    user = await user_service.update_user(db, user_id, update_data)
    return UserResponse.model_validate(user)
