# Development Plan: Booking API Service (Кинотеатр)

## Tech Stack
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + SQLAlchemy (async) + Alembic
- **Cache/Locks**: Redis
- **Message Queue**: Kafka
- **Auth**: JWT
- **Email**: SMTP (aiosmtplib)
- **Testing**: pytest + pytest-asyncio
- **CI/CD**: GitHub Actions
- **Container**: Docker + docker-compose

---

## Этап 1: Базовая структура проекта

- [ ] Создать структуру директорий `app/` с подпапками
- [ ] `pyproject.toml` — poetry dependencies
- [ ] `config.py` — Pydantic Settings (DB, Redis, Kafka, SMTP)
- [ ] `db.py` — async SQLAlchemy engine + session maker
- [ ] `redis.py` — Redis async connection
- [ ] `kafka.py` — Kafka producer setup
- [ ] `exceptions.py` — BookingConflictError, BookingNotFoundError, etc.
- [ ] `app/main.py` — FastAPI app с lifespan events (инициализация Redis/Kafka)

**Dependencies (pyproject.toml):**
```toml
[project]
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy[asyncio]",
    "asyncpg",
    "alembic",
    "pydantic-settings",
    "redis[hiredis]",
    "aiokafka",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "aiosmtplib",
    "email-validator",
    "httpx",
    "ruff",
    "mypy",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]
```

---

## Этап 2: Модели данных (Alembic)

### models/base.py
- `Base` = `DeclarativeBase`
- Базовый timestamp миксин: `created_at`, `updated_at`

### models/enums.py
- `UserRole` = Enum('user', 'admin')
- `BookingStatus` = Enum('confirmed', 'cancelled')

### models/user.py
```
User:
- id: int (PK)
- email: str (unique, index)
- hashed_password: str
- role: UserRole (default='user')
- is_active: bool (default=True)
- created_at: datetime
```

### models/hall.py
```
Hall:
- id: int (PK)
- name: str
- capacity: int (max seats in hall)
- hourly_rate: Decimal
- is_active: bool (default=True)
- created_at: datetime
```

### models/seat.py
```
Seat:
- id: int (PK)
- hall_id: int (FK → Hall)
- row: int
- number: int
- is_active: bool (default=True)
- UNIQUE CONSTRAINT: (hall_id, row, number)
```

### models/booking.py
```
Booking:
- id: int (PK)
- user_id: int (FK → User)
- hall_id: int (FK → Hall)
- start_time: datetime
- end_time: datetime
- total_price: Decimal
- status: BookingStatus (default='confirmed')
- created_at: datetime

BookingSeat (association table):
- id: int (PK)
- booking_id: int (FK → Booking)
- seat_id: int (FK → Seat)
```

### alembic/
- [ ] `alembic.ini` + `alembic/` directory
- [ ] Initial migration (head)

---

## Этап 3: Pydantic Schemas

### schemas/auth.py
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.user  # только admin может создать admin

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### schemas/user.py
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.user

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### schemas/hall.py
```python
class HallCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0)
    hourly_rate: Decimal = Field(..., gt=0)

class HallUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, gt=0)
    hourly_rate: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None

class HallResponse(BaseModel):
    id: int
    name: str
    capacity: int
    hourly_rate: Decimal
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### schemas/seat.py
```python
class SeatCreate(BaseModel):
    row: int = Field(..., ge=1)
    number: int = Field(..., ge=1)

class SeatResponse(BaseModel):
    id: int
    hall_id: int
    row: int
    number: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
```

### schemas/booking.py
```python
class BookingSeatCreate(BaseModel):
    seat_id: int

class BookingCreate(BaseModel):
    hall_id: int
    seat_ids: List[int] = Field(..., min_length=1)
    start_time: datetime
    end_time: datetime

class BookingResponse(BaseModel):
    id: int
    user_id: int
    hall_id: int
    hall_name: str
    seats: List[SeatResponse]
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: BookingStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

## Этап 4: Auth (JWT)

### core/security.py
```python
def hash_password(password: str) -> str
def verify_password(plain: str, hashed: str) -> bool
def create_access_token(data: dict, expires_delta: timedelta) -> str
def decode_access_token(token: str) -> dict
```

### core/dependencies.py
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]
async def get_current_user(token: str = Depends(get_token_from_header)) -> User
async def get_current_admin(user: User = Depends(get_current_user)) -> User
```

### services/auth_service.py
```python
async def register_user(db, email, password, role) -> User
async def authenticate_user(db, email, password) -> User
async def create_token(user: User) -> str
```

### routers/auth.py
```
POST /api/v1/auth/signup
POST /api/v1/auth/login
```

---

## Этап 5: CRUD ресурсов

### routers/users.py
```
GET  /api/v1/users/me          — профиль текущего пользователя
GET  /api/v1/users/            — список пользователей (admin only)
PATCH /api/v1/users/{id}       — обновить пользователя (admin only)
```

### routers/halls.py
```
GET   /api/v1/halls/           — список активных залов
GET   /api/v1/halls/{id}       — детали зала
POST  /api/v1/halls/           — создать зал (admin only)
PATCH /api/v1/halls/{id}       — обновить зал (admin only)
DELETE /api/v1/halls/{id}      — удалить зал (admin only)
```

### routers/seats.py
```
GET   /api/v1/halls/{hall_id}/seats/           — места в зале
POST  /api/v1/halls/{hall_id}/seats/           — создать места (admin only)
DELETE /api/v1/halls/{hall_id}/seats/{id}       — удалить место (admin only)
POST  /api/v1/halls/{hall_id}/seats/bulk        — bulk create (admin only)
```

---

## Этап 6: Бизнес-логика бронирования

### services/booking_service.py

```python
async def validate_time_slot(start_time, end_time) -> None:
    """Валидация: end > start, мин 30 мин, макс 8 часов, в пределах 09:00-23:00"""

async def check_seat_conflicts(
    db, hall_id, seat_ids, start_time, end_time, exclude_booking_id=None
) -> List[Seat]:
    """Проверка конфликтов мест. Возвращает список конфликтующих мест."""

async def acquire_redis_lock(redis, key, timeout=10) -> bool:
    """SETNX distributed lock"""

async def release_redis_lock(redis, key) -> None:
    """Удаление lock"""

async def calculate_total_price(
    hall: Hall, start_time: datetime, end_time: datetime
) -> Decimal:
    """total = hours * hourly_rate"""

async def create_booking(
    db, redis, user_id, hall_id, seat_ids, start_time, end_time
) -> Booking:
    """Основная логика:
    1. acquire lock
    2. validate time
    3. check seat conflicts
    4. calculate price
    5. save to DB
    6. send Kafka event
    7. release lock"""

async def cancel_booking(db, redis, booking_id, user_id) -> Booking:
    """Отмена бронирования:
    1. acquire lock
    2. check ownership
    3. update status
    4. send Kafka event
    5. release lock"""

async def get_available_slots(
    db, hall_id, date: date
) -> List[dict]:
    """Возвращает список доступных слотов на дату (кешируется в Redis)"""
```

### routers/bookings.py
```
GET  /api/v1/bookings/              — список бронирований текущего пользователя
GET  /api/v1/bookings/{id}         — детали бронирования
POST /api/v1/bookings/             — создать бронирование
DELETE /api/v1/bookings/{id}        — отменить бронирование
GET  /api/v1/bookings/halls/{id}/availability  — доступные слоты
```

---

## Этап 7: Kafka + Worker (Email notifications)

### Kafka events

```python
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

### services/notification_service.py
```python
async def send_booking_confirmation(email: str, booking: Booking) -> None:
    """Отправка email через SMTP"""

async def send_booking_cancellation(email: str, booking: Booking) -> None:
    """Отправка email об отмене"""
```

### worker.py
```python
# Kafka consumer
async def consume_booking_events():
    consumer = AIOKafkaConsumer('booking-events', bootstrap_servers=KAFKA_URL)
    async for msg in consumer:
        event = json.loads(msg.value)
        if event['type'] == 'booking_created':
            await send_booking_confirmation(...)
        elif event['type'] == 'booking_cancelled':
            await send_booking_cancellation(...)
```

---

## Этап 8: Docker + CI/CD

### Dockerfile
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis, kafka]
    env_file: .env

  db:
    image: postgres:16
    environment: POSTGRES_DB=booking_db

  redis:
    image: redis:7-alpine

  kafka:
    image: apache/kafka:3.7.0
    # Kafka + KRaft mode

  worker:
    build: .
    command: python worker.py
    depends_on: [kafka]
```

### .github/workflows/ci.yml
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .
      
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mypy app/
      
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v4
      
  docker:
    needs: [lint, typecheck, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build .
```

---

## Этап 9: Тесты (pytest)

### tests/conftest.py
```python
@pytest.fixture
async def db_session():
    # Async session с тестовой БД (SQLite или отдельный PostgreSQL)

@pytest.fixture
async def client(db_session):
    # AsyncClient с ASGITransport

@pytest.fixture
async def admin_user(db_session):
    # Создать admin юзера

@pytest.fixture
async def regular_user(db_session):
    # Создать обычного юзера

@pytest.fixture
async def auth_headers(admin_user):
    # JWT headers для admin

@pytest.fixture
async def test_hall(db_session):
    # Тестовый зал

@pytest.fixture
async def test_seats(db_session, test_hall):
    # Тестовые места
```

### tests/test_auth.py
- `test_register_success`
- `test_register_duplicate_email`
- `test_login_success`
- `test_login_invalid_password`
- `test_login_invalid_email`

### tests/test_halls.py
- `test_list_halls`
- `test_create_hall_as_admin`
- `test_create_hall_as_user_forbidden`
- `test_get_hall`

### tests/test_bookings.py
- `test_create_booking_success`
- `test_create_booking_seat_conflict`
- `test_create_booking_invalid_time`
- `test_cancel_booking`
- `test_cancel_other_user_booking_forbidden`
- `test_get_available_slots`

---

## Этап 10: Документация

### README.md
```markdown
# Booking API Service

REST API для бронирования залов кинотеатра.

## Stack
- FastAPI, PostgreSQL, Redis, Kafka, JWT, Docker

## Quick Start
```bash
docker-compose up --build
```

## API Docs
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Examples
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Create Booking
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hall_id":1,"seat_ids":[1,2],"start_time":"2026-03-30T14:00:00","end_time":"2026-03-30T16:00:00"}'
```
```

### AGENTS.md — обновить
- Добавить реальные пути к файлам после создания
- Уточнить конфиги (pytest.ini, ruff.toml, mypy.ini)

---

## Чеклист для резюме

| Технология | Этап | Статус |
|------------|------|--------|
| FastAPI async | 1-6 | ☐ |
| PostgreSQL + Alembic | 2 | ☐ |
| Redis (cache + locks) | 6 | ☐ |
| Kafka (event-driven) | 7 | ☐ |
| JWT auth (user + admin) | 4 | ☐ |
| GitHub Actions CI | 8 | ☐ |
| Docker + compose | 8 | ☐ |
| Unit + integration tests | 9 | ☐ |
| SMTP email notifications | 7 | ☐ |

---

## Порядок реализации

1. **Этап 1** — Базовая структура (config, db, redis, kafka, exceptions)
2. **Этап 2** — Модели + Alembic migration
3. **Этап 3** — Pydantic schemas
4. **Этап 4** — Auth (JWT)
5. **Этап 5** — CRUD ресурсов
6. **Этап 6** — Бронирования (核心 бизнес-логика)
7. **Этап 7** — Kafka + Worker
8. **Этап 8** — Docker + CI
9. **Этап 9** — Тесты
10. **Этап 10** — README

---

## Рефакторинг (после Этапа 10)

### Статус: В ПРОЦЕССЕ

### Этап Р1: Исправление критических багов ✅ ЗАВЕРШЁН
| # | Файл | Проблема | Коммит |
|---|------|----------|--------|
| 1 | `app/routers/bookings.py` | hardcoded `row=0, number=0` | `585c958` |
| 2 | `app/schemas/hall.py` | невалидный `decimal_places=2` | `55bff6b` |
| 3 | `tests/conftest.py` | строка вместо `UserRole` enum | `328b3d6` |
| 4 | `app/schemas/common.py` | отсутствовал `pagination_params()` | `43f93c1` |
| 5 | `app/services/booking_service.py` | `MissingGreenlet` после `refresh()` | `af83e37` |
| - | `tests/test_bookings.py` | активация пропущенных тестов | `6c39be9` |

### Этап Р2: Нейминг и унификация стилей ✅ ЗАВЕРШЁН
| # | Файл | Проблема | Действие | Статус |
|---|------|----------|----------|--------|
| 1 | `app/routers/auth.py` | Непоследовательный DI (нет `Annotated`) | Добавить `Annotated[...]` | ✅ |
| 2 | `app/core/dependencies.py` | `get_token_from_header` помечен как `async` | Убрать `async` | ✅ |
| 3 | `app/redis.py` | Неиспользуемые `acquire_lock`, `release_lock` | Удалить | ✅ |
| 4 | `app/exceptions.py` | Отсутствует `SeatAlreadyExistsError` | Добавить | ✅ |
| 5 | `app/routers/users.py`, `booking_service.py` | `ValueError` вместо кастомных исключений | Заменить | ✅ |

### Этап Р3: Архитектура (Service Layer) ✅ ЗАВЕРШЁН
| # | Компонент | Текущее | Целевое | Коммит |
|---|-----------|---------|---------|--------|
| 1 | Service Layer | Только `booking_service.py` | Добавить `user_service.py`, `hall_service.py` | `b046fa2` |
| 2 | Exception Handling | Разбросано по роутерам | Глобальные handlers в `main.py` | `40baaff` |
| 3 | Hall Validation | Дублируется 4 раза в `seats.py` | Вынести в `hall_service.py` | `b046fa2` |
| 4 | Booking Response | Дублируется 3 раза | Унифицировать | `cea9f68` |

### Этап Р4: Качество кода ✅ ЗАВЕРШЁН
| # | Файл | Проблема | Действие | Коммит |
|---|------|----------|----------|--------|
| 1 | `app/utils/` | Пустая папка | Удалить | `chore` |
| 2 | `app/` | 14 неиспользуемых импортов | Исправить ruff | `chore` |
| 3 | `alembic/`, `app/` | Неправильный порядок импортов | Исправить ruff | `chore` |
| 4 | `app/redis.py` | Неправильный формат | ruff format | `chore` |

### Этап Р5: Performance оптимизация ✅ ЗАВЕРШЁН
| # | Файл | Проблема | Решение | Коммит |
|---|------|----------|---------|--------|
| 1 | `app/services/booking_service.py` | `COUNT` через `len(all())` | `select(func.count())` | `chore` |
| 2 | `app/main.py` | Health check без проверки зависимостей | Полный check: DB + Redis + Kafka + таймауты | `chore` |

### Этап Р6: Очистка ✅ ЗАВЕРШЁН
| # | Задача | Действие | Коммит |
|---|--------|----------|--------|
| 1 | Проверить структуру проекта | Пустых папок нет | ✅ |
| 2 | Авто-исправления ruff | UP006, UP035, E712 | `chore` |
| 3 | Docker конфигурация | Проверена | ✅ |
| 4 | Тесты | 30/30 прошли | ✅ |

---

## Улучшения для мидл-позиции

### Этап У1: Rate Limiting ✅ ЗАВЕРШЁН
| # | Задача | Решение | Коммит |
|---|--------|---------|--------|
| 1 | Добавить rate limiting | slowapi + in-memory storage | `73cd662` |
| 2 | Настроить лимиты по группам | auth 5/min, bookings 10/min, etc. | `73cd662` |
| 3 | Кастомный 429 handler | JSONResponse с message | `73cd662` |
| 4 | Тесты | 30/30 прошли | `73cd662`
