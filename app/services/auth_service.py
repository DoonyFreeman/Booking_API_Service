from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions import UnauthorizedError, UserNotFoundError
from app.models import User
from app.models.enums import UserRole


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    role: UserRole = UserRole.user,
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("Email already registered")

    hashed_password = hash_password(password)

    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        is_active=True,
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("Invalid email or password")

    if not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("User is inactive")

    return user


def create_token(user: User) -> str:
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    }
    return create_access_token(token_data)
