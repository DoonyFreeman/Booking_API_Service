from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db import get_db
from app.exceptions import UnauthorizedError
from app.models import User
from app.models.enums import UserRole


def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header format")

    token = authorization.replace("Bearer ", "")
    if not token:
        raise UnauthorizedError("Missing token")

    return token


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise UnauthorizedError("Invalid or expired token") from None

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload") from None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("User not found") from None

    if not user.is_active:
        raise UnauthorizedError("User is inactive") from None

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]
