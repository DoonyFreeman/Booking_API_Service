from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import BookingSeat
    from app.models.hall import Hall


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint(
            "hall_id",
            "row",
            "number",
            name="uq_seat_position",
        ),
        Index("ix_seats_hall_id", "hall_id"),
        Index("ix_seats_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    hall_id: Mapped[int] = mapped_column(
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
    )
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    hall: Mapped["Hall"] = relationship("Hall", back_populates="seats")
    booking_seats: Mapped[List["BookingSeat"]] = relationship(
        "BookingSeat",
        back_populates="seat",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Seat(id={self.id}, hall={self.hall_id}, row={self.row}, number={self.number})>"
