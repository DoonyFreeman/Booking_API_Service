from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.seat import Seat


class BookingSeat(Base):
    __tablename__ = "booking_seats"
    __table_args__ = (
        Index("ix_booking_seats_booking_id", "booking_id"),
        Index("ix_booking_seats_seat_id", "seat_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )
    seat_id: Mapped[int] = mapped_column(
        ForeignKey("seats.id", ondelete="CASCADE"),
        nullable=False,
    )

    booking: Mapped["Booking"] = relationship("Booking", back_populates="booking_seats")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="booking_seats")

    def __repr__(self) -> str:
        return f"<BookingSeat(id={self.id}, booking={self.booking_id}, seat={self.seat_id})>"
