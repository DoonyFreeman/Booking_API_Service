from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HallCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0)
    hourly_rate: Decimal = Field(..., gt=0)


class HallUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, gt=0)
    hourly_rate: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None


class HallResponse(BaseModel):
    id: int
    name: str
    capacity: int
    hourly_rate: Decimal
    is_active: bool
    created_at: datetime
    total_seats: int = 0
    free_seats: int = 0

    model_config = ConfigDict(from_attributes=True)
