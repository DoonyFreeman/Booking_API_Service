# Agent Guidelines for Booking API Service (Кинотеатр)

## Project Overview

REST API для бронирования залов кинотеатра. Пользователи бронируют места в залах на определённое время.

---

## Development Progress

| Этап | Описание | Статус |
|------|---------|--------|
| 1 | Базовая структура проекта | ✅ Готово |
| 2 | Модели данных (User, Hall, Seat, Booking) | ✅ Готово |
| 3 | Pydantic Schemas | ✅ Готово |
| 4 | Auth (JWT) | ✅ Готово |
| 5 | CRUD ресурсов (users, halls, seats) | ✅ Готово |
| 6 | Бизнес-логика бронирования | ✅ Готово |
| 7 | Kafka + Worker (email) | ✅ Готово |
| 8 | Docker + CI/CD | ☐ |
| 9 | Тесты | ☐ |
| 10 | README + документация | ☐ |

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

### Setup
```bash
# Create venv and install
python -m venv venv && source venv/bin/activate
pip install -e .

# Copy environment
cp .env.example .env
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
pytest
pytest --cov=app --cov-report=html
pytest tests/test_auth.py -v
pytest tests/test_auth.py::test_register_success -v
pytest -k "test_create_booking"
```

### Docker
```bash
docker-compose up --build
docker-compose down
docker-compose logs -f api
```

---

## Current Project Structure

```
Booking_API_Service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # ✅ FastAPI app + lifespan
│   ├── config.py                 # ✅ Pydantic Settings
│   ├── db.py                     # ✅ async SQLAlchemy
│   ├── redis.py                  # ✅ Redis + lock helpers
│   ├── kafka.py                  # ✅ Kafka producer
│   ├── exceptions.py             # ✅ Custom HTTP exceptions
│   ├── models/
│   │   ├── __init__.py           # ✅ Exports all models
│   │   ├── base.py               # ✅ DeclarativeBase, TimestampMixin
│   │   ├── enums.py              # ✅ UserRole, BookingStatus
│   │   ├── user.py               # ✅ User model
│   │   ├── hall.py               # ✅ Hall model
│   │   ├── seat.py               # ✅ Seat model + UniqueConstraint
│   │   ├── booking.py            # ✅ Booking model + indexes
│   │   └── booking_seat.py       # ✅ BookingSeat (M2M)
│   ├── schemas/
│   │   ├── __init__.py           # ✅ Exports all schemas
│   │   ├── auth.py               # ✅ RegisterRequest, LoginRequest, TokenResponse
│   │   ├── user.py               # ✅ UserCreate, UserUpdate, UserResponse
│   │   ├── hall.py               # ✅ HallCreate, HallUpdate, HallResponse (+ free_seats)
│   │   ├── seat.py               # ✅ SeatCreate, SeatBulkCreate, SeatResponse
│   │   ├── booking.py            # ✅ BookingCreate, BookingResponse, BookingSeatResponse
│   │   └── common.py             # ✅ PaginationParams, PaginatedResponse<T>
│   ├── routers/                   # ✅ Auth router
│   │   ├── __init__.py           # ✅ Exports routers
│   │   ├── auth.py               # ✅ /api/v1/auth/signup, /login
│   │   ├── users.py              # /api/v1/users/me, /users/
│   │   ├── halls.py              # /api/v1/halls/
│   │   ├── seats.py              # /api/v1/halls/{id}/seats/
│   │   └── bookings.py          # /api/v1/bookings/
│   ├── services/                 # ✅ Auth service
│   │   ├── __init__.py           # ✅ Exports services
│   │   ├── auth_service.py       # ✅ register, authenticate, create_token
│   │   ├── booking_service.py
│   │   └── notification_service.py
│   ├── core/                     # ✅ Security
│   │   ├── __init__.py           # ✅ Exports security
│   │   ├── security.py           # ✅ hash, verify, JWT
│   │   └── dependencies.py      # ✅ get_current_user, get_current_admin
│   └── scripts/
│       ├── __init__.py
│       └── create_admin.py       # ✅ CLI for creating admin users
│   └── utils/
│       └── __init__.py
├── tests/                        # ☐ To be implemented
│   └── __init__.py
├── alembic/
│   ├── env.py                    # ✅ Async Alembic config
│   ├── script.py.mako
│   ├── versions/
│   │   └── 001_initial_tables.py # ✅ Migration
│   └── alembic.ini
├── docker-compose.yml             # ✅ PostgreSQL + Redis
├── pyproject.toml                # ✅ Dependencies
├── .env.example                  # ✅ Environment template
├── .gitignore
├── README.md
└── AGENTS.md
```

---

## Database Schema (PostgreSQL)

### Tables

**users** (✅ created)
- id, email (unique), hashed_password, role, is_active, created_at, updated_at
- Indexes: email (unique), role

**halls** (✅ created)
- id, name, capacity, hourly_rate, is_active, created_at, updated_at
- Indexes: name, is_active

**seats** (✅ created)
- id, hall_id (FK), row, number, is_active
- UniqueConstraint: (hall_id, row, number)
- Indexes: hall_id, is_active

**bookings** (✅ created)
- id, user_id (FK), hall_id (FK), start_time, end_time, total_price, status, created_at, updated_at
- Indexes: user_id, hall_id, start_time, end_time, status, (hall_id, start_time, end_time)

**booking_seats** (✅ created)
- id, booking_id (FK), seat_id (FK)
- Indexes: booking_id, seat_id

---

## API Endpoints (to be implemented)

### Auth
```
POST /api/v1/auth/signup    # Register (email, password)
POST /api/v1/auth/login     # Login → JWT token
```

### Users
```
GET  /api/v1/users/me       # Current user profile
GET  /api/v1/users/          # List users (admin)
PATCH /api/v1/users/{id}     # Update user (admin)
```

### Halls
```
GET   /api/v1/halls/         # List active halls
GET   /api/v1/halls/{id}    # Hall details (+ total_seats, free_seats)
POST  /api/v1/halls/        # Create hall (admin)
PATCH /api/v1/halls/{id}    # Update hall (admin)
DELETE /api/v1/halls/{id}   # Soft delete hall (admin)
```

### Seats
```
GET   /api/v1/halls/{hall_id}/seats/       # List seats in hall
POST  /api/v1/halls/{hall_id}/seats/       # Create seat (admin)
POST  /api/v1/halls/{hall_id}/seats/bulk    # Bulk create seats (admin)
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
class BookingConflictError(HTTPException):
    def __init__(self, detail: str = "Booking conflict"):
        super().__init__(status_code=409, detail=detail)

class HallNotFoundError(HTTPException):
    def __init__(self, detail: str = "Hall not found"):
        super().__init__(status_code=404, detail=detail)

class SeatNotFoundError(HTTPException):
    def __init__(self, detail: str = "Seat not found"):
        super().__init__(status_code=404, detail=detail)
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

## Redis Locks Pattern

```python
LOCK_PREFIX = "lock:booking:"
LOCK_TIMEOUT = 10

async def acquire_lock(client: redis.Redis, hall_id: int, date_str: str) -> bool:
    key = f"{LOCK_PREFIX}{hall_id}:{date_str}"
    return await client.set(key, "1", nx=True, ex=LOCK_TIMEOUT)

async def release_lock(client: redis.Redis, hall_id: int, date_str: str) -> None:
    key = f"{LOCK_PREFIX}{hall_id}:{date_str}"
    await client.delete(key)

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
# Producer (app/kafka.py)
async def send_booking_event(event_type: str, data: dict) -> None:
    event = {"type": event_type, **data}
    await producer.send_and_wait(settings.KAFKA_TOPIC_BOOKING_EVENTS, value=event)

# Event: BookingCreated
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

# Event: BookingCancelled
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
from app.db import get_db

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
# Application
APP_NAME=Booking API
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/booking_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_BOOKING_EVENTS=booking-events

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@booking.api

# Booking Limits
MIN_BOOKING_HOURS=1
MAX_BOOKING_HOURS=8
SESSION_START_HOUR=9
SESSION_END_HOUR=23
```

---

## Next Steps

1. **Этап 4: Auth (JWT)**
   - `app/core/security.py` — hash_password, verify_password, create_token, decode_token
   - `app/core/dependencies.py` — get_current_user, get_current_admin
   - `app/services/auth_service.py` — register, authenticate
   - `app/routers/auth.py` — /auth/signup, /auth/login

2. **Этап 5: CRUD ресурсов**
   - `app/routers/users.py`
   - `app/routers/halls.py`
   - `app/routers/seats.py`

3. **Этап 6: Бизнес-логика бронирования**
   - `app/services/booking_service.py`
   - `app/routers/bookings.py`
