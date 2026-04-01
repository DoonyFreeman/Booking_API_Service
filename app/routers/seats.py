from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.exceptions import HallNotFoundError, SeatNotFoundError
from app.models import Hall, Seat
from app.schemas import SeatBulkCreate, SeatCreate, SeatResponse

router = APIRouter(prefix="/halls/{hall_id}/seats", tags=["seats"])


@router.get("/", response_model=List[SeatResponse])
async def list_seats(
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> List[SeatResponse]:
    hall_result = await db.execute(select(Hall).where(Hall.id == hall_id))
    if not hall_result.scalar_one_or_none():
        raise HallNotFoundError()

    result = await db.execute(
        select(Seat)
        .where(Seat.hall_id == hall_id, Seat.is_active == True)
        .order_by(Seat.row, Seat.number)
    )
    seats = result.scalars().all()

    return [SeatResponse.model_validate(s) for s in seats]


@router.post(
    "/",
    response_model=SeatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_seat(
    hall_id: int,
    data: SeatCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> SeatResponse:
    hall_result = await db.execute(select(Hall).where(Hall.id == hall_id))
    if not hall_result.scalar_one_or_none():
        raise HallNotFoundError()

    seat = Seat(
        hall_id=hall_id,
        row=data.row,
        number=data.number,
        is_active=True,
    )

    db.add(seat)

    try:
        await db.flush()
        await db.refresh(seat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat {data.row}-{data.number} already exists",
        )

    return SeatResponse.model_validate(seat)


@router.post(
    "/bulk",
    response_model=List[SeatResponse],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_seats(
    hall_id: int,
    data: SeatBulkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> List[SeatResponse]:
    hall_result = await db.execute(select(Hall).where(Hall.id == hall_id))
    if not hall_result.scalar_one_or_none():
        raise HallNotFoundError()

    seats = []
    for row in range(1, data.rows + 1):
        for number in range(1, data.seats_per_row + 1):
            seat = Seat(
                hall_id=hall_id,
                row=row,
                number=number,
                is_active=True,
            )
            db.add(seat)
            seats.append(seat)

    try:
        await db.flush()
        for seat in seats:
            await db.refresh(seat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Some seats already exist",
        )

    return [SeatResponse.model_validate(s) for s in seats]


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(
    hall_id: int,
    seat_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> None:
    hall_result = await db.execute(select(Hall).where(Hall.id == hall_id))
    if not hall_result.scalar_one_or_none():
        raise HallNotFoundError()

    result = await db.execute(
        select(Seat).where(Seat.id == seat_id, Seat.hall_id == hall_id)
    )
    seat = result.scalar_one_or_none()

    if not seat:
        raise SeatNotFoundError()

    seat.is_active = False
    await db.flush()
