import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import HallNotFoundError, SeatAlreadyExistsError, SeatNotFoundError
from app.services import seat_service


class TestListSeats:
    @pytest.mark.asyncio
    async def test_list_seats_returns_only_active(
        self, db_session: AsyncSession, test_hall_db, test_seat_db
    ) -> None:
        inactive_seat = test_seat_db.__class__(
            hall_id=test_hall_db.id, row=2, number=1, is_active=False
        )
        db_session.add(inactive_seat)
        await db_session.flush()

        seats = await seat_service.list_seats(db_session, test_hall_db.id)
        assert len(seats) == 1
        assert seats[0].id == test_seat_db.id

    @pytest.mark.asyncio
    async def test_list_seats_hall_not_found(self, db_session: AsyncSession) -> None:
        with pytest.raises(HallNotFoundError):
            await seat_service.list_seats(db_session, 99999)


class TestCreateSeat:
    @pytest.mark.asyncio
    async def test_create_seat_success(
        self, db_session: AsyncSession, test_hall_db
    ) -> None:
        seat = await seat_service.create_seat(
            db=db_session,
            hall_id=test_hall_db.id,
            row=1,
            number=1,
        )
        assert seat.row == 1
        assert seat.number == 1
        assert seat.is_active is True

    @pytest.mark.asyncio
    async def test_create_seat_duplicate(
        self, db_session: AsyncSession, test_seat_db
    ) -> None:
        with pytest.raises(SeatAlreadyExistsError) as exc:
            await seat_service.create_seat(
                db=db_session,
                hall_id=test_seat_db.hall_id,
                row=test_seat_db.row,
                number=test_seat_db.number,
            )
        assert "already exists" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_create_seat_hall_not_found(self, db_session: AsyncSession) -> None:
        with pytest.raises(HallNotFoundError):
            await seat_service.create_seat(
                db=db_session,
                hall_id=99999,
                row=1,
                number=1,
            )


class TestBulkCreateSeats:
    @pytest.mark.asyncio
    async def test_bulk_create_seats_success(
        self, db_session: AsyncSession, test_hall_db
    ) -> None:
        seats = await seat_service.bulk_create_seats(
            db=db_session,
            hall_id=test_hall_db.id,
            rows=2,
            seats_per_row=3,
        )
        assert len(seats) == 6

    @pytest.mark.asyncio
    async def test_bulk_create_seats_with_conflict(
        self, db_session: AsyncSession, test_seat_db
    ) -> None:
        with pytest.raises(SeatAlreadyExistsError) as exc:
            await seat_service.bulk_create_seats(
                db=db_session,
                hall_id=test_seat_db.hall_id,
                rows=1,
                seats_per_row=1,
            )
        assert "already exist" in str(exc.value.detail)


class TestDeleteSeat:
    @pytest.mark.asyncio
    async def test_delete_seat_success(
        self, db_session: AsyncSession, test_seat_db
    ) -> None:
        await seat_service.delete_seat(
            db=db_session,
            hall_id=test_seat_db.hall_id,
            seat_id=test_seat_db.id,
        )
        await db_session.refresh(test_seat_db)
        assert test_seat_db.is_active is False

    @pytest.mark.asyncio
    async def test_delete_seat_not_found(
        self, db_session: AsyncSession, test_hall_db
    ) -> None:
        with pytest.raises(SeatNotFoundError):
            await seat_service.delete_seat(
                db=db_session,
                hall_id=test_hall_db.id,
                seat_id=99999,
            )
