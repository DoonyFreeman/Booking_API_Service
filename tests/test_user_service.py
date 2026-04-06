import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import UserNotFoundError
from app.services import user_service


class TestGetUserById:
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(
        self, db_session: AsyncSession, test_user
    ) -> None:
        user = await user_service.get_user_by_id(db_session, test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession) -> None:
        user = await user_service.get_user_by_id(db_session, 99999)
        assert user is None


class TestListUsers:
    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, db_session: AsyncSession, test_user
    ) -> None:
        users, total = await user_service.list_users(
            db=db_session,
            page=1,
            page_size=10,
        )
        assert total >= 1
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_list_users_empty(self, db_session: AsyncSession) -> None:
        users, total = await user_service.list_users(
            db=db_session,
            page=1,
            page_size=10,
        )
        assert total == 0
        assert users == []


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_update_user_success(
        self, db_session: AsyncSession, test_user
    ) -> None:
        updated = await user_service.update_user(
            db=db_session,
            user_id=test_user.id,
            data={"email": "updated@test.com"},
        )
        assert updated.email == "updated@test.com"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session: AsyncSession) -> None:
        with pytest.raises(UserNotFoundError):
            await user_service.update_user(
                db=db_session,
                user_id=99999,
                data={"email": "updated@test.com"},
            )
