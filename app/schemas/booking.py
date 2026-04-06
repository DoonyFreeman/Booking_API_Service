from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingStatus


class BookingCreate(BaseModel):
    hall_id: int
    seat_ids: list[int] = Field(..., min_length=1)
    start_time: datetime
    end_time: datetime


class BookingSeatResponse(BaseModel):
    id: int
    row: int
    number: int

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    hall_id: int
    hall_name: str
    seats: list[BookingSeatResponse]
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    bookings: list[BookingResponse]
    total: int


class TimeSlotResponse(BaseModel):
    hour: int
    available: bool
    total_seats: int
    free_seats: int
    booked_seats: int
