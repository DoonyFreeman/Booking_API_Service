from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import UserNotFoundError
from app.models import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).order_by(User.id).offset(offset).limit(page_size)
    )
    users = list(result.scalars().all())

    return users, total


async def update_user(db: AsyncSession, user_id: int, data: dict) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError()

    for field, value in data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user
