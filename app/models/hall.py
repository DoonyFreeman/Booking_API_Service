from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.seat import Seat


class Hall(Base, TimestampMixin):
    __tablename__ = "halls"
    __table_args__ = (
        Index("ix_halls_name", "name"),
        Index("ix_halls_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    seats: Mapped[list["Seat"]] = relationship(
        "Seat",
        back_populates="hall",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="hall",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Hall(id={self.id}, name={self.name})>"
