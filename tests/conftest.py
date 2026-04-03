from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import User
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
    user.role = "admin"
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


def create_app():
    from app.main import create_app as _create_app

    return _create_app()
