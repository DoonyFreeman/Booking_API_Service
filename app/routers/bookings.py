from datetime import date
from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db import get_db
from app.models import Seat
from app.redis import get_redis
from app.schemas import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    BookingSeatResponse,
    PaginatedResponse,
    PaginationParams,
    TimeSlotResponse,
)
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


def booking_to_response(booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hall_id=booking.hall_id,
        hall_name=booking.hall.name if booking.hall else "Unknown",
        seats=[
            BookingSeatResponse(id=bs.seat_id, row=0, number=0)
            for bs in booking.booking_seats
        ],
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_price=booking.total_price,
        status=booking.status,
        created_at=booking.created_at,
    )


@router.get("/", response_model=PaginatedResponse[BookingResponse])
async def list_bookings(
    pagination: PaginationParams,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedResponse[BookingResponse]:
    bookings, total = await booking_service.get_user_bookings(
        db=db,
        user_id=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    items = [booking_to_response(b) for b in bookings]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookingResponse:
    booking = await booking_service.get_booking_by_id(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )

    seats_result = await db.execute(
        select(Seat).where(Seat.id.in_([bs.seat_id for bs in booking.booking_seats]))
    )
    seats = {s.id: s for s in seats_result.scalars().all()}

    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hall_id=booking.hall_id,
        hall_name=booking.hall.name if booking.hall else "Unknown",
        seats=[
            BookingSeatResponse(
                id=bs.seat_id,
                row=seats[bs.seat_id].row,
                number=seats[bs.seat_id].number,
            )
            for bs in booking.booking_seats
        ],
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_price=booking.total_price,
        status=booking.status,
        created_at=booking.created_at,
    )


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    data: BookingCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: redis.Redis = Depends(get_redis),
) -> BookingResponse:
    booking = await booking_service.create_booking(
        db=db,
        redis_client=redis_client,
        user_id=current_user.id,
        hall_id=data.hall_id,
        seat_ids=data.seat_ids,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    seats_result = await db.execute(select(Seat).where(Seat.id.in_(data.seat_ids)))
    seats = {s.id: s for s in seats_result.scalars().all()}

    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hall_id=booking.hall_id,
        hall_name=booking.hall.name if booking.hall else "Unknown",
        seats=[
            BookingSeatResponse(
                id=bs.seat_id,
                row=seats[bs.seat_id].row,
                number=seats[bs.seat_id].number,
            )
            for bs in booking.booking_seats
        ],
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_price=booking.total_price,
        status=booking.status,
        created_at=booking.created_at,
    )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await booking_service.cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )


@router.get(
    "/halls/{hall_id}/availability",
    response_model=list[TimeSlotResponse],
)
async def get_availability(
    hall_id: int,
    date: date,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: redis.Redis = Depends(get_redis),
) -> list[TimeSlotResponse]:
    slots = await booking_service.get_available_slots(
        db=db,
        redis_client=redis_client,
        hall_id=hall_id,
        target_date=date,
    )

    return [TimeSlotResponse(**slot) for slot in slots]
