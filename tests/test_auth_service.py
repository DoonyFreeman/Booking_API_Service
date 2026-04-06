import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import UnauthorizedError
from app.services import auth_service


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: AsyncSession) -> None:
        user = await auth_service.register_user(
            db=db_session,
            email="newuser@test.com",
            password="securepass123",
        )
        assert user.email == "newuser@test.com"
        assert user.role == "user"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, db_session: AsyncSession
    ) -> None:
        await auth_service.register_user(
            db=db_session,
            email="duplicate@test.com",
            password="password123",
        )

        with pytest.raises(ValueError) as exc:
            await auth_service.register_user(
                db=db_session,
                email="duplicate@test.com",
                password="password123",
            )
        assert "already registered" in str(exc.value)


class TestAuthenticateUser:
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession) -> None:
        await auth_service.register_user(
            db=db_session,
            email="authuser@test.com",
            password="password123",
        )

        user = await auth_service.authenticate_user(
            db=db_session,
            email="authuser@test.com",
            password="password123",
        )
        assert user.email == "authuser@test.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self, db_session: AsyncSession
    ) -> None:
        await auth_service.register_user(
            db=db_session,
            email="wrongpass@test.com",
            password="correctpass123",
        )

        with pytest.raises(UnauthorizedError) as exc:
            await auth_service.authenticate_user(
                db=db_session,
                email="wrongpass@test.com",
                password="wrongpass123",
            )
        assert "Invalid email or password" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session: AsyncSession) -> None:
        with pytest.raises(UnauthorizedError) as exc:
            await auth_service.authenticate_user(
                db=db_session,
                email="nonexistent@test.com",
                password="password123",
            )
        assert "Invalid email or password" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, db_session: AsyncSession) -> None:
        user = await auth_service.register_user(
            db=db_session,
            email="inactive@test.com",
            password="password123",
        )
        user.is_active = False
        await db_session.flush()

        with pytest.raises(UnauthorizedError) as exc:
            await auth_service.authenticate_user(
                db=db_session,
                email="inactive@test.com",
                password="password123",
            )
        assert "inactive" in str(exc.value.detail)


class TestCreateToken:
    @pytest.mark.asyncio
    async def test_create_token_generates_valid_jwt(
        self, db_session: AsyncSession
    ) -> None:
        user = await auth_service.register_user(
            db=db_session,
            email="tokenuser@test.com",
            password="password123",
        )

        token = auth_service.create_token(user)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
