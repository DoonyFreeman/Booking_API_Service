from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.models.booking_seat import BookingSeat
    from app.models.hall import Hall
    from app.models.user import User


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_user_id", "user_id"),
        Index("ix_bookings_hall_id", "hall_id"),
        Index("ix_bookings_start_time", "start_time"),
        Index("ix_bookings_end_time", "end_time"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_hall_time", "hall_id", "start_time", "end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    hall_id: Mapped[int] = mapped_column(
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    status: Mapped[BookingStatus] = mapped_column(
        String(20),
        default=BookingStatus.confirmed,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="bookings")
    hall: Mapped["Hall"] = relationship("Hall", back_populates="bookings")
    booking_seats: Mapped[List["BookingSeat"]] = relationship(
        "BookingSeat",
        back_populates="booking",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, hall={self.hall_id}, status={self.status})>"
