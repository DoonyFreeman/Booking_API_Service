from pydantic import BaseModel, ConfigDict, Field


class SeatCreate(BaseModel):
    row: int = Field(..., ge=1)
    number: int = Field(..., ge=1)


class SeatBulkCreate(BaseModel):
    rows: int = Field(..., ge=1, description="Number of rows")
    seats_per_row: int = Field(..., ge=1, description="Number of seats per row")


class SeatResponse(BaseModel):
    id: int
    hall_id: int
    row: int
    number: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
