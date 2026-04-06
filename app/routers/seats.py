from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.limiter import limiter, seats_limit
from app.schemas import SeatBulkCreate, SeatCreate, SeatResponse
from app.services import seat_service

router = APIRouter(prefix="/halls/{hall_id}/seats", tags=["seats"])


@router.get("/", response_model=list[SeatResponse])
@limiter.limit(seats_limit)
async def list_seats(
    request: Request,
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> list[SeatResponse]:
    seats = await seat_service.list_seats(db, hall_id)
    return [SeatResponse.model_validate(s) for s in seats]


@router.post(
    "/",
    response_model=SeatResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(seats_limit)
async def create_seat(
    request: Request,
    hall_id: int,
    data: SeatCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> SeatResponse:
    seat = await seat_service.create_seat(
        db=db,
        hall_id=hall_id,
        row=data.row,
        number=data.number,
    )
    return SeatResponse.model_validate(seat)


@router.post(
    "/bulk",
    response_model=list[SeatResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(seats_limit)
async def bulk_create_seats(
    request: Request,
    hall_id: int,
    data: SeatBulkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> list[SeatResponse]:
    seats = await seat_service.bulk_create_seats(
        db=db,
        hall_id=hall_id,
        rows=data.rows,
        seats_per_row=data.seats_per_row,
    )
    return [SeatResponse.model_validate(s) for s in seats]


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(seats_limit)
async def delete_seat(
    request: Request,
    hall_id: int,
    seat_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> None:
    await seat_service.delete_seat(db, hall_id, seat_id)
