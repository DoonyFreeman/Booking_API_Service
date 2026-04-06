from datetime import date
from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import CurrentUser
from app.db import get_db
from app.limiter import bookings_limit, limiter
from app.redis import get_redis
from app.schemas import (
    BookingCreate,
    BookingResponse,
    PaginatedResponse,
    TimeSlotResponse,
    pagination_params,
)
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get(
    "/",
    response_model=PaginatedResponse[BookingResponse],
    summary="Список бронирований",
    description="Возвращает список бронирований текущего пользователя с пагинацией.",
)
@limiter.limit(bookings_limit)
async def list_bookings(
    request: Request,
    pagination: Annotated[..., Depends(pagination_params)],
    current_user: CurrentUser,
    db: Annotated[..., Depends(get_db)],
) -> PaginatedResponse[BookingResponse]:
    bookings, total = await booking_service.get_user_bookings(
        db=db,
        user_id=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    items = [await booking_service.build_booking_response(db, b) for b in bookings]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Получить бронирование",
    description="Возвращает детали конкретного бронирования по ID. Доступно только владельцу бронирования.",
)
@limiter.limit(bookings_limit)
async def get_booking(
    request: Request,
    booking_id: int,
    current_user: CurrentUser,
    db: Annotated[..., Depends(get_db)],
) -> BookingResponse:
    booking = await booking_service.get_booking_by_id(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )
    return await booking_service.build_booking_response(db, booking)


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать бронирование",
    description="Создает новое бронирование для указанных мест и времени. Время бронирования должно быть кратно часу, минимальная длительность - 1 час, максимальная - 8 часов.",
)
@limiter.limit(bookings_limit)
async def create_booking(
    request: Request,
    data: BookingCreate,
    current_user: CurrentUser,
    db: Annotated[..., Depends(get_db)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
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
    return await booking_service.build_booking_response(db, booking)


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отменить бронирование",
    description="Отменяет бронирование (мягкое удаление). Доступно только владельцу бронирования.",
)
@limiter.limit(bookings_limit)
async def cancel_booking(
    request: Request,
    booking_id: int,
    current_user: CurrentUser,
    db: Annotated[..., Depends(get_db)],
) -> None:
    await booking_service.cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
    )


@router.get(
    "/halls/{hall_id}/availability",
    response_model=list[TimeSlotResponse],
    summary="Доступные временные слоты",
    description="Возвращает список доступных временных слотов для бронирования в указанном зале на указанную дату.",
)
@limiter.limit(bookings_limit)
async def get_availability(
    request: Request,
    hall_id: int,
    date: date,
    current_user: CurrentUser,
    db: Annotated[..., Depends(get_db)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> list[TimeSlotResponse]:
    slots = await booking_service.get_available_slots(
        db=db,
        redis_client=redis_client,
        hall_id=hall_id,
        target_date=date,
    )

    return [TimeSlotResponse(**slot) for slot in slots]
