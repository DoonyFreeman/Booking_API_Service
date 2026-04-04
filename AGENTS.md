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
| 8 | Docker + CI/CD | ✅ Готово |
| 9 | Тесты | ✅ Готово |
| 10 | README + документация | ✅ Готово |

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

## Quick Start

### 1. Start all services with Docker

```bash
docker-compose up --build
```

API will be available at: http://localhost:8000/docs

### 2. Create admin user

```bash
docker exec booking_api python -m app.scripts.create_admin --email admin@test.com --password secret123
```

### 3. Use Swagger UI

1. Open: http://localhost:8000/docs
2. Login: POST /api/v1/auth/login
3. Copy `access_token` from response
4. Click **"Authorize"** button (🔓)
5. Paste token **WITHOUT** `Bearer ` prefix
6. Click **"Authorize"** → **"Close"**

---

## Commands

### Setup (Local Development)
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
# Start all services
docker-compose up --build

# Start specific service
docker-compose up -d api

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build api
docker-compose up -d --build worker
```

### Kafka Messages (View events)
```bash
docker exec booking_kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --topic booking-events --from-beginning --bootstrap-server localhost:9092
```

---

## Current Project Structure

```
Booking_API_Service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + lifespan
│   ├── config.py                 # Pydantic Settings
│   ├── db.py                     # async SQLAlchemy
│   ├── redis.py                  # Redis + lock helpers
│   ├── kafka.py                  # Kafka producer
│   ├── worker.py                 # Kafka consumer worker
│   ├── exceptions.py             # Custom HTTP exceptions
│   ├── models/
│   │   ├── __init__.py          # Exports all models
│   │   ├── base.py              # DeclarativeBase, TimestampMixin
│   │   ├── enums.py             # UserRole, BookingStatus
│   │   ├── user.py              # User model
│   │   ├── hall.py              # Hall model
│   │   ├── seat.py              # Seat model
│   │   ├── booking.py           # Booking model
│   │   └── booking_seat.py      # BookingSeat (M2M)
│   ├── schemas/
│   │   ├── __init__.py          # Exports all schemas
│   │   ├── auth.py              # RegisterRequest, LoginRequest, TokenResponse
│   │   ├── user.py              # UserCreate, UserUpdate, UserResponse
│   │   ├── hall.py              # HallCreate, HallUpdate, HallResponse
│   │   ├── seat.py              # SeatCreate, SeatBulkCreate, SeatResponse
│   │   ├── booking.py           # BookingCreate, BookingResponse
│   │   └── common.py            # PaginationParams, PaginatedResponse<T>
│   ├── routers/
│   │   ├── __init__.py          # Exports routers
│   │   ├── auth.py              # /api/v1/auth/signup, /login
│   │   ├── users.py             # /api/v1/users/me, /users/
│   │   ├── halls.py             # /api/v1/halls/
│   │   ├── seats.py             # /api/v1/halls/{id}/seats/
│   │   └── bookings.py          # /api/v1/bookings/
│   ├── services/
│   │   ├── __init__.py         # Exports services
│   │   ├── auth_service.py      # register, authenticate, create_token
│   │   ├── booking_service.py   # Booking CRUD + validation
│   │   └── notification_service.py # Email sending
│   ├── core/
│   │   ├── __init__.py          # Exports security
│   │   ├── security.py          # hash, verify, JWT
│   │   └── dependencies.py       # get_current_user, get_current_admin
│   └── scripts/
│       └── create_admin.py       # CLI for creating admin users
├── tests/                       # To be implemented
├── alembic/
│   ├── env.py                   # Async Alembic config
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_tables.py
├── docker-compose.yml            # PostgreSQL + Redis + Kafka + API + Worker
├── Dockerfile                    # API container
├── pyproject.toml
├── .env.example
├── .gitignore
└── AGENTS.md
```

---

## Database Schema (PostgreSQL)

### Tables

**users**
- id, email (unique), hashed_password, role, is_active, created_at, updated_at
- Indexes: email (unique), role

**halls**
- id, name, capacity, hourly_rate, is_active, created_at, updated_at
- Indexes: name, is_active

**seats**
- id, hall_id (FK), row, number, is_active
- UniqueConstraint: (hall_id, row, number)
- Indexes: hall_id, is_active

**bookings**
- id, user_id (FK), hall_id (FK), start_time, end_time, total_price, status, created_at, updated_at
- Indexes: user_id, hall_id, start_time, end_time, status, (hall_id, start_time, end_time)

**booking_seats**
- id, booking_id (FK), seat_id (FK)
- Indexes: booking_id, seat_id

---

## API Endpoints

### Auth
```
POST /api/v1/auth/signup    # Register (email, password)
POST /api/v1/auth/login    # Login → JWT token
```

### Users
```
GET  /api/v1/users/me       # Current user profile
GET  /api/v1/users/         # List users (admin)
PATCH /api/v1/users/{id}    # Update user (admin)
```

### Halls
```
GET   /api/v1/halls/           # List active halls
GET   /api/v1/halls/{id}       # Hall details (+ total_seats, free_seats)
POST  /api/v1/halls/           # Create hall (admin)
PATCH /api/v1/halls/{id}       # Update hall (admin)
DELETE /api/v1/halls/{id}      # Soft delete hall (admin)
```

### Seats
```
GET   /api/v1/halls/{hall_id}/seats/      # List seats in hall
POST  /api/v1/halls/{hall_id}/seats/      # Create seat (admin)
POST  /api/v1/halls/{hall_id}/seats/bulk   # Bulk create seats (admin)
DELETE /api/v1/halls/{hall_id}/seats/{id}  # Delete seat (admin)
```

### Bookings
```
GET  /api/v1/bookings/                           # User's bookings
GET  /api/v1/bookings/{id}                       # Booking details
POST /api/v1/bookings/                           # Create booking
DELETE /api/v1/bookings/{id}                     # Cancel booking
GET  /api/v1/bookings/halls/{id}/availability    # Available slots
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
from sqlalchemy import select
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
LOCK_TIMEOUT = 10

async def create_booking(...):
    date_str = start_time.date().isoformat()
    hour = start_time.hour
    lock_key = f"lock:hall:{hall_id}:{date_str}:{hour}"
    
    if not await redis_client.set(lock_key, "1", nx=True, ex=LOCK_TIMEOUT):
        raise BookingConflictError("Another booking in progress for this time slot")
    
    try:
        # ... business logic ...
    finally:
        await redis_client.delete(lock_key)
```

---

## Kafka Events

### Producer (app/kafka.py)
```python
async def send_booking_event(event_type: str, data: dict) -> None:
    event = {"type": event_type, **data}
    await producer.send_and_wait(settings.KAFKA_TOPIC_BOOKING_EVENTS, value=event)
```

### Event: BookingCreated
```json
{
    "type": "booking_created",
    "booking_id": 123,
    "user_id": 1,
    "user_email": "user@example.com",
    "hall_name": "Зал 1",
    "start_time": "2026-03-30T14:00:00",
    "end_time": "2026-03-30T16:00:00",
    "total_price": "200.00"
}
```

### Event: BookingCancelled
```json
{
    "type": "booking_cancelled",
    "booking_id": 123,
    "user_id": 1,
    "user_email": "user@example.com",
    "hall_name": "Зал 1"
}
```

### Kafka Worker (app/worker.py)
- Connects to Kafka with retry logic (10 attempts, 5s delay)
- Consumes `booking-events` topic
- Processes `booking_created` and `booking_cancelled` events
- Sends email notifications via SMTP

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
- Use `selectinload()` for eager loading relationships

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

Tests are located in `tests/` directory:
- `tests/conftest.py` - fixtures for client, db_session, auth tokens
- `tests/test_auth.py` - authentication tests
- `tests/test_halls.py` - hall CRUD tests
- `tests/test_seats.py` - seat CRUD tests
- `tests/test_bookings.py` - booking tests

Run tests:
```bash
pytest tests/ -v
pytest --cov=app --cov-report=html  # with coverage
pytest tests/test_auth.py -v          # specific file
pytest tests/test_auth.py::test_register_success -v  # specific test
```

Fixtures available in conftest.py:
- `client` - AsyncClient with test app
- `db_session` - SQLite in-memory database session
- `registered_user` - Creates a regular user
- `admin_user` - Creates an admin user
- `user_token` / `admin_token` - JWT tokens
- `auth_headers` / `admin_headers` - Auth headers for requests
- `test_hall` - Creates a test hall
- `test_seat` - Creates a test seat

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

### Docker Environment

For Docker-compose, environment variables override `.env`:

```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/booking_db
  - REDIS_URL=redis://redis:6379/0
  - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

---

## Important Notes for Agents

### Common Issues and Solutions

1. **ModuleNotFoundError: No module named 'app'**
   - Use `python -m app.worker` instead of `python app/worker.py`

2. **Kafka connection refused from worker**
   - Use `kafka:9092` (Docker hostname) not `localhost:9092`
   - Worker does NOT use `.env` file (env vars passed via `environment:` in compose)

3. **SQLAlchemy MissingGreenlet error**
   - Use `selectinload()` for eager loading relationships
   - Don't access lazy-loaded relationships outside async context

4. **Swagger Authorize - token rejected**
   - Paste token **WITHOUT** `Bearer ` prefix
   - Swagger auto-adds `Bearer ` prefix

### Dockerfile Notes

- API uses `.env` file (copied from `.env.example`)
- Worker does NOT use `.env` (uses environment variables from compose)
- Both use same Dockerfile, different commands

---

## Next Steps

### All Completed (1-10)
- [x] Этап 1: Базовая структура проекта
- [x] Этап 2: Модели данных
- [x] Этап 3: Pydantic Schemas
- [x] Этап 4: Auth (JWT)
- [x] Этап 5: CRUD ресурсов
- [x] Этап 6: Бизнес-логика бронирования
- [x] Этап 7: Kafka + Worker
- [x] Этап 8: Docker + CI/CD
- [x] Этап 9: Тесты (pytest)
- [x] Этап 10: Финализировать документацию

### Рефакторинг
- [x] Р1: Исправление критических багов (6 коммитов)
- [x] Р2: Нейминг и унификация стилей
- [x] Р3: Архитектура (Service Layer)
- [ ] Р4: Качество кода
- [ ] Р5: Performance оптимизация
- [ ] Р6: Очистка

Подробный план: см. `DEVELOPMENT_PLAN.md`

---

## Git Workflow

```bash
# Check status
git status

# Add and commit
git add <files>
git commit -m "fix: description of changes"

# Push to remote
git push

# Or push with auto-stash
git stash && git pull --rebase && git stash pop
```

### Commit Message Convention

```
<type>: <short description>

<body>

<footer>
```

Types: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`, `chore:`
