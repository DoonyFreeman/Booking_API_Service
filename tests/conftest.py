from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import Hall, Seat, User
from app.models.enums import UserRole
from app.redis import get_redis

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.data[key] = value

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def delete(self, key: str) -> int:
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    async def close(self) -> None:
        pass


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_kafka() -> None:
    with patch("app.kafka.send_booking_event", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def auto_mock_kafka() -> None:
    with patch("app.kafka.send_booking_event", new_callable=AsyncMock):
        yield


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis() -> FakeRedis:
        return FakeRedis()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    with patch("app.kafka.init_kafka", new_callable=AsyncMock):
        with patch("app.kafka.close_kafka", new_callable=AsyncMock):
            with patch("app.kafka.send_booking_event", new_callable=AsyncMock):
                with patch("app.redis.init_redis", new_callable=AsyncMock):
                    with patch("app.redis.close_redis", new_callable=AsyncMock):
                        transport = ASGITransport(app=app)
                        async with AsyncClient(
                            transport=transport,
                            base_url="http://test",
                        ) as ac:
                            yield ac


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@test.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return {"email": "user@test.com", "password": "password123"}


@pytest.fixture
async def admin_user(client: AsyncClient, db_session: AsyncSession) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "admin@test.com",
            "password": "adminpass123",
        },
    )
    assert response.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == "admin@test.com")
    )
    user = result.scalar_one()
    user.role = UserRole.admin
    await db_session.commit()

    return {"email": "admin@test.com", "password": "adminpass123"}


@pytest.fixture
async def user_token(client: AsyncClient, registered_user: dict) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def admin_token(client: AsyncClient, admin_user: dict) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def test_hall(client: AsyncClient, admin_headers: dict) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/halls/",
        json={
            "name": "Test Hall",
            "capacity": 50,
            "hourly_rate": 100.00,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def test_seat(
    client: AsyncClient, admin_headers: dict, test_hall: dict
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/halls/{test_hall['id']}/seats/",
        json={
            "row": 1,
            "number": 1,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="testuser@test.com",
        hashed_password="hashed_password",
        role=UserRole.user,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    admin = User(
        email="testadmin@test.com",
        hashed_password="hashed_password",
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_hall_db(db_session: AsyncSession) -> Hall:
    hall = Hall(
        name="Test Hall DB",
        capacity=50,
        hourly_rate=Decimal("100.00"),
        is_active=True,
    )
    db_session.add(hall)
    await db_session.flush()
    await db_session.refresh(hall)
    return hall


@pytest.fixture
async def test_seat_db(db_session: AsyncSession, test_hall_db: Hall) -> Seat:
    seat = Seat(
        hall_id=test_hall_db.id,
        row=1,
        number=1,
        is_active=True,
    )
    db_session.add(seat)
    await db_session.flush()
    await db_session.refresh(seat)
    return seat


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


def create_app():
    from app.limiter import limiter
    from app.main import create_app as _create_app

    app = _create_app()
    app.state.limiter = limiter
    limiter.enabled = False
    return app
