# Agent Guidelines for Booking API Service (Кинотеатр)

## Project Overview

REST API для бронирования залов кинотеатра. Пользователи бронируют места в залах на определённое время.

## Development Plan

См. `DEVELOPMENT_PLAN.md` для полного плана реализации.

---

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + SQLAlchemy (async) + Alembic
- **Cache/Locks**: Redis
- **Message Queue**: Kafka
- **Auth**: JWT tokens
- **Email**: SMTP (aiosmtplib)
- **Testing**: pytest + pytest-asyncio
- **CI/CD**: GitHub Actions
- **Container**: Docker + docker-compose

---

## Commands

### Virtual Environment
```bash
python -m venv venv && source venv/bin/activate
poetry install
```

### Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Linting & Formatting
```bash
ruff format .
ruff check .
mypy app/
```

### Database Migrations (Alembic)
```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
alembic downgrade -1
```

### Testing
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Single test file
pytest tests/test_auth.py -v

# Single test function
pytest tests/test_auth.py::test_register_success -v

# Pattern match
pytest -k "test_create_booking"
```

### Docker
```bash
docker-compose up --build
docker-compose down
docker-compose logs -f api
```

---

## Project Structure

```
app/
├── main.py                    # FastAPI app + lifespan
├── config.py                  # Pydantic Settings
├── db.py                      # async SQLAlchemy
├── redis.py                   # Redis connection
├── kafka.py                   # Kafka producer
├── exceptions.py              # Custom exceptions
├── models/
│   ├── base.py                # DeclarativeBase
│   ├── enums.py               # UserRole, BookingStatus
│   ├── user.py
│   ├── hall.py
│   ├── seat.py
│   └── booking.py
├── schemas/
│   ├── auth.py                # Login, Register
│   ├── user.py
│   ├── hall.py
│   ├── seat.py
│   └── booking.py
├── routers/
│   ├── auth.py                # /api/v1/auth/
│   ├── users.py               # /api/v1/users/
│   ├── halls.py              # /api/v1/halls/
│   ├── seats.py              # /api/v1/halls/{id}/seats/
│   └── bookings.py           # /api/v1/bookings/
├── services/
│   ├── auth_service.py
│   ├── booking_service.py    # Core: conflicts, locks, price
│   └── notification_service.py
├── core/
│   ├── security.py            # JWT, password hashing
│   └── dependencies.py        # get_db, get_current_user
└── utils/
    └── datetime_utils.py
tests/
├── conftest.py
├── test_auth.py
├── test_halls.py
└── test_bookings.py
worker.py                      # Kafka consumer
```

---

## API Endpoints

### Auth
```
POST /api/v1/auth/signup    # Register (email, password)
POST /api/v1/auth/login     # Login → JWT token
```

### Users
```
GET  /api/v1/users/me       # Current user profile
GET  /api/v1/users/         # List users (admin)
PATCH /api/v1/users/{id}     # Update user (admin)
```

### Halls
```
GET   /api/v1/halls/        # List active halls
GET   /api/v1/halls/{id}    # Hall details
POST  /api/v1/halls/        # Create hall (admin)
PATCH /api/v1/halls/{id}    # Update hall (admin)
```

### Seats
```
GET   /api/v1/halls/{hall_id}/seats/   # List seats in hall
POST  /api/v1/halls/{hall_id}/seats/   # Create seat (admin)
POST  /api/v1/halls/{hall_id}/seats/bulk   # Bulk create (admin)
DELETE /api/v1/halls/{hall_id}/seats/{id}  # Delete seat (admin)
```

### Bookings
```
GET  /api/v1/bookings/                              # User's bookings
GET  /api/v1/bookings/{id}                          # Booking details
POST /api/v1/bookings/                              # Create booking
DELETE /api/v1/bookings/{id}                        # Cancel booking
GET  /api/v1/bookings/halls/{id}/availability       # Available slots
```

---

## Code Style Guidelines

### Imports Order (ruff)
1. Standard library
2. Third-party
3. Local application

```python
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingCreate
```

### Type Annotations
Required for all function parameters and return types.

### Naming
| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `booking_service.py` |
| Classes | PascalCase | `BookingService` |
| Functions | snake_case | `create_booking` |
| Variables | snake_case | `booking_id` |
| Constants | UPPER_SNAKE | `LOCK_TIMEOUT` |

---

## Error Handling

### HTTP Exceptions
```python
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Seats A1, A2 are already booked for this time"
)
```

### Custom Exceptions (app/exceptions.py)
```python
class BookingConflictError(Exception):
    pass

class SeatNotFoundError(Exception):
    pass

class HallNotFoundError(Exception):
    pass
```

### Async Error Handling
```python
try:
    result = await create_booking(...)
except BookingConflictError as e:
    raise HTTPException(status_code=409, detail=str(e))
except Exception as e:
    logger.error(f"Booking failed: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

---

## Pydantic Schemas (examples)

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import List

class BookingCreate(BaseModel):
    hall_id: int
    seat_ids: List[int] = Field(..., min_length=1)
    start_time: datetime
    end_time: datetime

class BookingResponse(BaseModel):
    id: int
    hall_id: int
    hall_name: str
    seats: List[SeatResponse]
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

## SQLAlchemy Models (examples)

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint('hall_id', 'row', 'number', name='uq_seat_position'),
    )

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    row = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
```

---

## Redis Locks Pattern

```python
import redis.asyncio as redis

LOCK_PREFIX = "lock:booking:"
LOCK_TIMEOUT = 10

async def acquire_lock(redis_client: redis.Redis, hall_id: int, date: str) -> bool:
    key = f"{LOCK_PREFIX}{hall_id}:{date}"
    return await redis_client.set(key, "1", nx=True, ex=LOCK_TIMEOUT)

async def release_lock(redis_client: redis.Redis, hall_id: int, date: str) -> None:
    key = f"{LOCK_PREFIX}{hall_id}:{date}"
    await redis_client.delete(key)

async def create_booking(...):
    date_str = start_time.date().isoformat()
    if not await acquire_lock(redis_client, hall_id, date_str):
        raise BookingConflictError("Another booking in progress")
    try:
        # ... business logic ...
    finally:
        await release_lock(redis_client, hall_id, date_str)
```

---

## Kafka Events

```python
# Producer (services/booking_service.py)
async def publish_booking_event(kafka_producer, event_type: str, data: dict):
    event = {"type": event_type, **data}
    await kafka_producer.send("booking-events", value=event)

# Events
{
    "type": "booking_created",
    "booking_id": 123,
    "user_email": "user@example.com",
    "hall_name": "Зал 1",
    "seats": ["A1", "A2"],
    "start_time": "2026-03-30T14:00:00",
    "end_time": "2026-03-30T16:00:00",
    "total_price": "200.00"
}

{
    "type": "booking_cancelled",
    "booking_id": 123,
    "user_email": "user@example.com",
    "hall_name": "Зал 1"
}
```

---

## Database Sessions

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@router.post("/bookings/", response_model=BookingResponse)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...
```

---

## Async/Await Rules

- All route handlers: `async def`
- All service functions: `async def`
- Always `await` async operations
- Use `asyncio.gather()` for concurrent operations
- Never block with sync operations

---

## Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Booking created: %s", booking_id)
logger.warning("Conflict detected for seats: %s", seat_ids)
logger.error("Redis lock failed: %s", error)
```

---

## Testing Guidelines

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/bookings/",
        json={
            "hall_id": 1,
            "seat_ids": [1, 2],
            "start_time": "2026-03-30T14:00:00",
            "end_time": "2026-03-30T16:00:00"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
```

---

## Status Codes

| Code | Usage |
|------|-------|
| 200 | GET, PATCH |
| 201 | POST (create) |
| 204 | DELETE |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Not authorized (not admin) |
| 404 | Resource not found |
| 409 | Booking conflict |
| 500 | Internal error |

---

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/booking_db
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
