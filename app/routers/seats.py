from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser
from app.db import get_db
from app.schemas import SeatBulkCreate, SeatCreate, SeatResponse
from app.services import seat_service

router = APIRouter(prefix="/halls/{hall_id}/seats", tags=["seats"])


@router.get("/", response_model=List[SeatResponse])
async def list_seats(
    hall_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> List[SeatResponse]:
    seats = await seat_service.list_seats(db, hall_id)
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
    seat = await seat_service.create_seat(
        db=db,
        hall_id=hall_id,
        row=data.row,
        number=data.number,
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
    seats = await seat_service.bulk_create_seats(
        db=db,
        hall_id=hall_id,
        rows=data.rows,
        seats_per_row=data.seats_per_row,
    )
    return [SeatResponse.model_validate(s) for s in seats]


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(
    hall_id: int,
    seat_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: AdminUser,
) -> None:
    await seat_service.delete_seat(db, hall_id, seat_id)
