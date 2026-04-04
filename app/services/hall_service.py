from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import HallNotFoundError
from app.models import Hall


async def get_hall_or_raise(db: AsyncSession, hall_id: int) -> Hall:
    result = await db.execute(select(Hall).where(Hall.id == hall_id))
    hall = result.scalar_one_or_none()
    if not hall:
        raise HallNotFoundError()
    return hall


async def get_active_hall_or_raise(db: AsyncSession, hall_id: int) -> Hall:
    result = await db.execute(
        select(Hall).where(Hall.id == hall_id, Hall.is_active == True)
    )
    hall = result.scalar_one_or_none()
    if not hall:
        raise HallNotFoundError("Hall not found or inactive")
    return hall


async def get_hall_with_seats(db: AsyncSession, hall_id: int) -> Hall:
    result = await db.execute(
        select(Hall).options(selectinload(Hall.seats)).where(Hall.id == hall_id)
    )
    hall = result.scalar_one_or_none()
    if not hall:
        raise HallNotFoundError()
    return hall


async def list_active_halls(db: AsyncSession) -> list[Hall]:
    result = await db.execute(
        select(Hall)
        .where(Hall.is_active == True)
        .options(selectinload(Hall.seats))
        .order_by(Hall.id)
    )
    return list(result.scalars().all())
