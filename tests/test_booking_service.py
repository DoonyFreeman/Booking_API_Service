from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BookingConflictError,
    BookingNotFoundError,
    HallNotFoundError,
    InvalidTimeSlotError,
    SeatNotFoundError,
    UserNotFoundError,
)
from app.services import booking_service


class TestValidateTimeSlot:
    @pytest.mark.asyncio
    async def test_validate_time_slot_end_before_start(self) -> None:
        start = datetime(2026, 4, 10, 14, 0, 0)
        end = datetime(2026, 4, 10, 13, 0, 0)

        with pytest.raises(InvalidTimeSlotError) as exc:
            await booking_service.validate_time_slot(start, end)
        assert "End time must be after start time" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_validate_time_slot_too_short(self) -> None:
        start = datetime(2026, 4, 10, 14, 0, 0)
        end = datetime(2026, 4, 10, 14, 30, 0)

        with pytest.raises(InvalidTimeSlotError) as exc:
            await booking_service.validate_time_slot(start, end)
        assert "Minimum booking duration" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_validate_time_slot_too_long(self) -> None:
        start = datetime(2026, 4, 10, 14, 0, 0)
        end = datetime(2026, 4, 10, 23, 0, 0)

        with pytest.raises(InvalidTimeSlotError) as exc:
            await booking_service.validate_time_slot(start, end)
        assert "Maximum booking duration" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_validate_time_slot_not_on_hour(self) -> None:
        start = datetime(2026, 4, 10, 14, 30, 0)
        end = datetime(2026, 4, 10, 16, 0, 0)

        with pytest.raises(InvalidTimeSlotError) as exc:
            await booking_service.validate_time_slot(start, end)
        assert "must start and end on the hour" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_validate_time_slot_before_session_start(self) -> None:
        start = datetime(2026, 4, 10, 8, 0, 0)
        end = datetime(2026, 4, 10, 10, 0, 0)

        with pytest.raises(InvalidTimeSlotError) as exc:
            await booking_service.validate_time_slot(start, end)
        assert "cannot start before" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_validate_time_slot_after_session_end(self) -> None:
        start = datetime(2026, 4, 10, 20, 0, 0)
        end = datetime(2026, 4, 10, 22, 0, 0)

        result = await booking_service.validate_time_slot(start, end)
        assert result is None


class TestValidateSeatsExist:
    @pytest.mark.asyncio
    async def test_validate_seats_exist_all_found(
        self, db_session: AsyncSession, test_seat_db
    ) -> None:
        seats = await booking_service.validate_seats_exist(
            db_session, test_seat_db.hall_id, [test_seat_db.id]
        )
        assert len(seats) == 1
        assert seats[0].id == test_seat_db.id

    @pytest.mark.asyncio
    async def test_validate_seats_exist_missing_seats(
        self, db_session: AsyncSession, test_hall_db
    ) -> None:
        with pytest.raises(SeatNotFoundError) as exc:
            await booking_service.validate_seats_exist(
                db_session, test_hall_db.id, [99999]
            )
        assert "Seats not found" in str(exc.value.detail)


class TestCheckSeatConflicts:
    @pytest.mark.asyncio
    async def test_check_seat_conflicts_no_conflict(
        self, db_session: AsyncSession, test_hall_db, test_seat_db
    ) -> None:
        result = await booking_service.check_seat_conflicts(
            db_session,
            test_hall_db.id,
            [test_seat_db.id],
            datetime(2026, 4, 10, 14, 0, 0),
            datetime(2026, 4, 10, 16, 0, 0),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_check_seat_conflicts_with_conflict(
        self,
        db_session: AsyncSession,
        test_hall_db,
        test_seat_db,
        test_user,
    ) -> None:
        from app.models import Booking, BookingSeat
        from app.models.enums import BookingStatus

        booking = Booking(
            user_id=test_user.id,
            hall_id=test_hall_db.id,
            start_time=datetime(2026, 4, 10, 14, 0, 0),
            end_time=datetime(2026, 4, 10, 16, 0, 0),
            total_price=Decimal("200.00"),
            status=BookingStatus.confirmed,
        )
        db_session.add(booking)
        await db_session.flush()

        booking_seat = BookingSeat(booking_id=booking.id, seat_id=test_seat_db.id)
        db_session.add(booking_seat)
        await db_session.flush()

        with pytest.raises(BookingConflictError) as exc:
            await booking_service.check_seat_conflicts(
                db_session,
                test_hall_db.id,
                [test_seat_db.id],
                datetime(2026, 4, 10, 14, 0, 0),
                datetime(2026, 4, 10, 16, 0, 0),
            )
        assert "already booked" in str(exc.value.detail)


class TestCalculatePrice:
    def test_calculate_price_basic(self) -> None:
        price = booking_service.calculate_price(Decimal("100.00"), 2)
        assert price == Decimal("200.00")

    def test_calculate_price_single_hour(self) -> None:
        price = booking_service.calculate_price(Decimal("150.00"), 1)
        assert price == Decimal("150.00")

    def test_calculate_price_zero_hours(self) -> None:
        price = booking_service.calculate_price(Decimal("100.00"), 0)
        assert price == Decimal("0")


class TestCreateBooking:
    @pytest.mark.skip(reason="Requires Kafka")
    @pytest.mark.asyncio
    async def test_create_booking_success(
        self,
        db_session: AsyncSession,
        test_hall_db,
        test_seat_db,
        test_user,
        fake_redis,
    ) -> None:
        pass

    @pytest.mark.asyncio
    async def test_create_booking_hall_not_found(
        self, db_session: AsyncSession, test_user, fake_redis
    ) -> None:
        with pytest.raises(HallNotFoundError):
            await booking_service.create_booking(
                db=db_session,
                redis_client=fake_redis,
                user_id=test_user.id,
                hall_id=99999,
                seat_ids=[],
                start_time=datetime(2026, 4, 10, 14, 0, 0),
                end_time=datetime(2026, 4, 10, 16, 0, 0),
            )

    @pytest.mark.asyncio
    async def test_create_booking_user_not_found(
        self, db_session: AsyncSession, test_hall_db, fake_redis
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await booking_service.create_booking(
                db=db_session,
                redis_client=fake_redis,
                user_id=99999,
                hall_id=test_hall_db.id,
                seat_ids=[],
                start_time=datetime(2026, 4, 10, 14, 0, 0),
                end_time=datetime(2026, 4, 10, 16, 0, 0),
            )


class TestCancelBooking:
    @pytest.mark.skip(reason="Requires Kafka")
    @pytest.mark.asyncio
    async def test_cancel_booking_success(
        self, db_session: AsyncSession, test_hall_db, test_user
    ) -> None:
        pass

    @pytest.mark.asyncio
    async def test_cancel_booking_not_found(
        self, db_session: AsyncSession, test_user
    ) -> None:
        with pytest.raises(BookingNotFoundError):
            await booking_service.cancel_booking(
                db=db_session,
                booking_id=99999,
                user_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_cancel_booking_wrong_user(
        self, db_session: AsyncSession, test_hall_db, test_user
    ) -> None:
        from app.models import Booking
        from app.models.enums import BookingStatus

        other_user_id = test_user.id + 100
        booking = Booking(
            user_id=other_user_id,
            hall_id=test_hall_db.id,
            start_time=datetime(2026, 4, 10, 14, 0, 0),
            end_time=datetime(2026, 4, 10, 16, 0, 0),
            total_price=Decimal("200.00"),
            status=BookingStatus.confirmed,
        )
        db_session.add(booking)
        await db_session.commit()

        with pytest.raises(BookingNotFoundError):
            await booking_service.cancel_booking(
                db=db_session,
                booking_id=booking.id,
                user_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_cancel_booking_already_cancelled(
        self, db_session: AsyncSession, test_hall_db, test_user
    ) -> None:
        from app.models import Booking
        from app.models.enums import BookingStatus

        booking = Booking(
            user_id=test_user.id,
            hall_id=test_hall_db.id,
            start_time=datetime(2026, 4, 10, 14, 0, 0),
            end_time=datetime(2026, 4, 10, 16, 0, 0),
            total_price=Decimal("200.00"),
            status=BookingStatus.cancelled,
        )
        db_session.add(booking)
        await db_session.commit()

        with pytest.raises(BookingConflictError) as exc:
            await booking_service.cancel_booking(
                db=db_session,
                booking_id=booking.id,
                user_id=test_user.id,
            )
        assert "already cancelled" in str(exc.value.detail)
