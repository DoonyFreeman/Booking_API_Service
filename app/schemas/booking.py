from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingStatus


class BookingCreate(BaseModel):
    hall_id: int
    seat_ids: List[int] = Field(..., min_length=1)
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
    seats: List[BookingSeatResponse]
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total: int
