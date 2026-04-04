from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import SeatAlreadyExistsError, SeatNotFoundError
from app.models import Seat
from app.services.hall_service import get_hall_or_raise


async def list_seats(db: AsyncSession, hall_id: int) -> list[Seat]:
    await get_hall_or_raise(db, hall_id)
    result = await db.execute(
        select(Seat)
        .where(Seat.hall_id == hall_id, Seat.is_active == True)
        .order_by(Seat.row, Seat.number)
    )
    return list(result.scalars().all())


async def create_seat(
    db: AsyncSession,
    hall_id: int,
    row: int,
    number: int,
) -> Seat:
    await get_hall_or_raise(db, hall_id)
    seat = Seat(hall_id=hall_id, row=row, number=number, is_active=True)
    db.add(seat)
    try:
        await db.flush()
        await db.refresh(seat)
        return seat
    except IntegrityError:
        await db.rollback()
        raise SeatAlreadyExistsError(f"Seat {row}-{number} already exists")


async def bulk_create_seats(
    db: AsyncSession,
    hall_id: int,
    rows: int,
    seats_per_row: int,
) -> list[Seat]:
    await get_hall_or_raise(db, hall_id)
    seats = []
    for row in range(1, rows + 1):
        for number in range(1, seats_per_row + 1):
            seat = Seat(hall_id=hall_id, row=row, number=number, is_active=True)
            db.add(seat)
            seats.append(seat)
    try:
        await db.flush()
        for seat in seats:
            await db.refresh(seat)
        return seats
    except IntegrityError:
        await db.rollback()
        raise SeatAlreadyExistsError("Some seats already exist")


async def delete_seat(db: AsyncSession, hall_id: int, seat_id: int) -> None:
    await get_hall_or_raise(db, hall_id)
    result = await db.execute(
        select(Seat).where(Seat.id == seat_id, Seat.hall_id == hall_id)
    )
    seat = result.scalar_one_or_none()
    if not seat:
        raise SeatNotFoundError()
    seat.is_active = False
    await db.flush()
