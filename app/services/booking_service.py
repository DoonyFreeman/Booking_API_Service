import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import redis.asyncio as redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.exceptions import (
    BookingConflictError,
    BookingNotFoundError,
    HallNotFoundError,
    InvalidTimeSlotError,
    SeatNotFoundError,
    UserNotFoundError,
)
from app.kafka import send_booking_event
from app.models import Booking, BookingSeat, Hall, Seat, User
from app.models.enums import BookingStatus
from app.schemas import BookingResponse, BookingSeatResponse

CACHE_TTL = 300
CACHE_PREFIX = "slots:hall:"


async def build_booking_response(
    db: AsyncSession,
    booking: Booking,
) -> BookingResponse:
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


async def validate_time_slot(start_time: datetime, end_time: datetime) -> None:
    if end_time <= start_time:
        raise InvalidTimeSlotError("End time must be after start time")

    duration = end_time - start_time
    hours = duration.total_seconds() / 3600

    if hours < settings.MIN_BOOKING_HOURS:
        raise InvalidTimeSlotError(
            f"Minimum booking duration is {settings.MIN_BOOKING_HOURS} hour(s)"
        )

    if hours > settings.MAX_BOOKING_HOURS:
        raise InvalidTimeSlotError(
            f"Maximum booking duration is {settings.MAX_BOOKING_HOURS} hours"
        )

    if start_time.minute != 0 or end_time.minute != 0:
        raise InvalidTimeSlotError("Booking must start and end on the hour")

    if start_time.hour < settings.SESSION_START_HOUR:
        raise InvalidTimeSlotError(
            f"Booking cannot start before {settings.SESSION_START_HOUR}:00"
        )

    if end_time.hour > settings.SESSION_END_HOUR:
        raise InvalidTimeSlotError(
            f"Booking cannot end after {settings.SESSION_END_HOUR}:00"
        )


async def validate_seats_exist(
    db: AsyncSession,
    hall_id: int,
    seat_ids: list[int],
) -> list[Seat]:
    result = await db.execute(
        select(Seat).where(
            Seat.id.in_(seat_ids),
            Seat.hall_id == hall_id,
            Seat.is_active,
        )
    )
    seats = list(result.scalars().all())

    if len(seats) != len(seat_ids):
        found_ids = {s.id for s in seats}
        missing = set(seat_ids) - found_ids
        raise SeatNotFoundError(f"Seats not found: {missing}")

    return seats


async def check_seat_conflicts(
    db: AsyncSession,
    hall_id: int,
    seat_ids: list[int],
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> list[Seat]:
    query = (
        select(Seat)
        .join(BookingSeat, BookingSeat.seat_id == Seat.id)
        .join(Booking, Booking.id == BookingSeat.booking_id)
        .where(
            Seat.id.in_(seat_ids),
            Booking.hall_id == hall_id,
            Booking.status == BookingStatus.confirmed,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
    )

    if exclude_booking_id:
        query = query.where(Booking.id != exclude_booking_id)

    result = await db.execute(query)
    conflicting_seats = list(result.scalars().all())

    if conflicting_seats:
        seat_numbers = [f"{s.row}-{s.number}" for s in conflicting_seats]
        raise BookingConflictError(
            f"Seats already booked for this time: {', '.join(seat_numbers)}"
        )

    return conflicting_seats


def calculate_price(hourly_rate: Decimal, hours: int) -> Decimal:
    return hourly_rate * hours


async def create_booking(
    db: AsyncSession,
    redis_client: redis.Redis,
    user_id: int,
    hall_id: int,
    seat_ids: list[int],
    start_time: datetime,
    end_time: datetime,
) -> Booking:
    hall_result = await db.execute(
        select(Hall).where(Hall.id == hall_id, Hall.is_active)
    )
    hall = hall_result.scalar_one_or_none()
    if not hall:
        raise HallNotFoundError("Hall not found or inactive")

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError()

    await validate_time_slot(start_time, end_time)
    await validate_seats_exist(db, hall_id, seat_ids)
    await check_seat_conflicts(db, hall_id, seat_ids, start_time, end_time)

    date_str = start_time.date().isoformat()
    hour = start_time.hour
    lock_key = f"lock:hall:{hall_id}:{date_str}:{hour}"

    if not await redis_client.set(
        lock_key, "1", nx=True, ex=settings.REDIS_LOCK_TIMEOUT
    ):
        raise BookingConflictError("Another booking in progress for this time slot")

    try:
        await check_seat_conflicts(db, hall_id, seat_ids, start_time, end_time)

        hours = int((end_time - start_time).total_seconds() / 3600)
        total_price = calculate_price(hall.hourly_rate, hours)

        booking = Booking(
            user_id=user_id,
            hall_id=hall_id,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price,
            status=BookingStatus.confirmed,
        )
        db.add(booking)
        await db.flush()

        for seat_id in seat_ids:
            booking_seat = BookingSeat(booking_id=booking.id, seat_id=seat_id)
            db.add(booking_seat)

        await db.flush()
        await db.refresh(booking)

        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.hall), selectinload(Booking.booking_seats))
            .where(Booking.id == booking.id)
        )
        booking = result.scalar_one()

        await send_booking_event(
            "booking_created",
            {
                "booking_id": booking.id,
                "user_id": user_id,
                "user_email": user.email,
                "hall_name": hall.name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_price": str(total_price),
            },
        )

        return booking

    finally:
        await redis_client.delete(lock_key)


async def cancel_booking(
    db: AsyncSession,
    booking_id: int,
    user_id: int,
) -> Booking:
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.user), selectinload(Booking.hall))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise BookingNotFoundError()

    if booking.user_id != user_id:
        raise BookingNotFoundError("Booking not found")

    if booking.status == BookingStatus.cancelled:
        raise BookingConflictError("Booking already cancelled")

    user_email = booking.user.email if booking.user else ""
    hall_name = booking.hall.name if booking.hall else "Unknown"

    booking.status = BookingStatus.cancelled
    await db.flush()
    await db.refresh(booking)

    await send_booking_event(
        "booking_cancelled",
        {
            "booking_id": booking.id,
            "user_id": user_id,
            "user_email": user_email,
            "hall_name": hall_name,
        },
    )

    return booking


async def get_booking_by_id(
    db: AsyncSession,
    booking_id: int,
    user_id: int | None = None,
) -> Booking:
    query = (
        select(Booking)
        .options(selectinload(Booking.hall), selectinload(Booking.booking_seats))
        .where(Booking.id == booking_id)
    )

    if user_id is not None:
        query = query.where(Booking.user_id == user_id)

    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise BookingNotFoundError()

    return booking


async def get_user_bookings(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Booking], int]:
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.hall), selectinload(Booking.booking_seats))
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = list(result.scalars().all())

    return bookings, total


async def get_available_slots(
    db: AsyncSession,
    redis_client: redis.Redis,
    hall_id: int,
    target_date: date,
) -> list[dict[str, Any]]:
    cache_key = f"{CACHE_PREFIX}{hall_id}:{target_date.isoformat()}"

    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    slots = await _calculate_slots(db, hall_id, target_date)

    await redis_client.setex(cache_key, CACHE_TTL, json.dumps(slots))

    return slots


async def _calculate_slots(
    db: AsyncSession,
    hall_id: int,
    target_date: date,
) -> list[dict[str, Any]]:
    hall_result = await db.execute(
        select(Hall).where(Hall.id == hall_id, Hall.is_active)
    )
    hall = hall_result.scalar_one_or_none()
    if not hall:
        raise HallNotFoundError()

    seats_result = await db.execute(
        select(Seat).where(Seat.hall_id == hall_id, Seat.is_active)
    )
    total_seats = len(seats_result.scalars().all())

    start_datetime = datetime.combine(
        target_date, datetime.min.time().replace(hour=settings.SESSION_START_HOUR)
    )
    end_datetime = datetime.combine(
        target_date, datetime.min.time().replace(hour=settings.SESSION_END_HOUR)
    )

    bookings_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_seats))
        .where(
            Booking.hall_id == hall_id,
            Booking.status == BookingStatus.confirmed,
            Booking.start_time >= start_datetime,
            Booking.end_time <= end_datetime,
        )
    )
    bookings = bookings_result.scalars().all()

    booked_seats_by_hour: dict[int, set[int]] = {
        h: set() for h in range(settings.SESSION_START_HOUR, settings.SESSION_END_HOUR)
    }

    for booking in bookings:
        start_hour = booking.start_time.hour
        end_hour = booking.end_time.hour
        for hour in range(start_hour, end_hour):
            for bs in booking.booking_seats:
                booked_seats_by_hour[hour].add(bs.seat_id)

    slots = []
    for hour in range(settings.SESSION_START_HOUR, settings.SESSION_END_HOUR):
        booked = len(booked_seats_by_hour[hour])
        free = total_seats - booked
        slots.append(
            {
                "hour": hour,
                "available": free > 0,
                "total_seats": total_seats,
                "free_seats": free,
                "booked_seats": booked,
            }
        )

    return slots
