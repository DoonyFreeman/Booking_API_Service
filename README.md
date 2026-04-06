# Booking API Service

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?style=flat&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=flat&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-red?style=flat&logo=redis)
![Docker](https://img.shields.io/badge/Docker-3.7-blue?style=flat&logo=docker)
![Kafka](https://img.shields.io/badge/Kafka-3.7-black?style=flat)

REST API для бронирования залов кинотеатра. Управление залами, местами, временными слотами и email-уведомлениями через event-driven архитектуру.

---

## Содержание

1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Что я изучил](#что-я-изучил)
5. [Архитектура](#архитектура)
6. [Тестирование](#тестирование)
7. [API](#api)
8. [Конфигурация](#конфигурация)
9. [Лицензия](#лицензия)

---

## Quick Start

Клонируем, запускаем, готово:

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/booking-api-service.git
cd booking-api-service

# Запускаем всё
docker-compose up --build

# Создаём админа (после первого запуска)
docker exec booking_api python -m app.scripts.create_admin \
  --email admin@test.com \
  --password secret123
```

Документация API доступна по адресу: **http://localhost:8000/docs**

---

## Features

| Компонент | Статус | Описание |
|-----------|--------|----------|
| Authentication | ✅ | JWT токены + role-based access (user/admin) |
| Halls CRUD | ✅ | Создание, обновление, удаление залов |
| Seats CRUD | ✅ | Управление местами + bulk создание |
| Bookings | ✅ | Создание, отмена, список бронирований |
| Availability | ✅ | Проверка свободных слотов (кешируется в Redis) |
| Kafka Worker | ✅ | Обработка событий бронирования |
| Rate Limiting | ✅ | Лимиты запросов через slowapi |
| Graceful Shutdown | ✅ | Корректное завершение процессов |
| Health Checks | ✅ | Проверка состояния сервисов |
| Alembic Migrations | ✅ | Миграции БД в Docker |
| Tests | ✅ | 70% покрытие pytest |

---

## Tech Stack

| Технология | Зачем |
|------------|-------|
| **FastAPI** | Асинхронный REST API с auto-docs |
| **PostgreSQL** | Основная база данных |
| **Redis** | Кеширование + distributed locks |
| **Kafka** | Очередь событий для email-уведомлений |
| **SQLAlchemy** | ORM (async режим) |
| **JWT** | Аутентификация через токены |
| **Docker** | Контейнеризация всех сервисов |

---

## Что я изучил

В процессе работы над проектом разобрался в следующих темах:

- **Async/await в Python** — работа с async SQLAlchemy, правильная организация асинхронного кода
- **Distributed locking** — использование Redis для предотвращения race conditions при бронировании
- **Event-driven архитектура** — Kafka как message broker, обработка событий в отдельном worker
- **Docker orchestration** — docker-compose, multi-container приложения, healthchecks
- ** Alembic миграции** — версионирование схемы БД, применение миграций при деплое
- **Rate limiting** — реализация через slowapi, разные лимиты для разных endpoint групп
- **Graceful shutdown** — корректная обработка SIGTERM, завершение соединений

---

## Архитектура

### High-level компоненты

```mermaid
graph TB
    subgraph API
        R[Routes] --> S[Services]
        S --> M[Models]
    end
    
    subgraph Infrastructure
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Kafka[(Kafka)]
        SMTP[📧 SMTP]
    end
    
    R --> DB
    R --> Redis
    R --> Kafka
    
    subgraph Worker
        W[Email Worker]
    end
    
    Kafka --> W
    W --> SMTP
```

### Flow бронирования

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant R as Redis
    participant D as DB
    participant K as Kafka
    participant W as Worker
    
    U->>A: POST /bookings
    A->>A: Validate JWT
    A->>R: Acquire lock
    R-->>A: Lock OK
    A->>D: Check seat conflicts
    D-->>A: No conflicts
    A->>D: Save booking
    A->>K: Send event
    A-->>U: 201 Created
    K->>W: booking_created
    W->>W: Send email
```

### Component overview

```
┌─────────────────────────────────────────────────────────┐
│                    booking_api                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │  Auth   │  │ Halls   │  │  Seats  │  │ Bookings │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────┬────┘    │
│       └───────────┴──────────┴──────────────┘          │
│                         │                               │
│              ┌──────────┴──────────┐                   │
│              │   Service Layer     │                    │
│              └──────────┬──────────┘                   │
└─────────────────────────┼───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌─────────┐      ┌─────────┐      ┌──────────┐
   │PostgreSQL│     │  Redis  │      │  Kafka   │
   └─────────┘      └─────────┘      └────┬─────┘
                                         │
                                   ┌─────┴─────┐
                                   │   Worker  │
                                   └───────────┘
```

---

## Тестирование

Запускаем тесты:

```bash
pytest tests/ -v
```

Результат: **70 passed, 2 skipped**

С покрытием:

```bash
pytest --cov=app --cov-report=html
# Отчёт в htmlcov/index.html
```

Тесты разделены на:
- Unit-тесты сервисов (`test_*_service.py`)
- Интеграционные тесты API (`test_*.py`)

---

## API

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /api/v1/auth/signup | Public | Регистрация |
| POST | /api/v1/auth/login | Public | Вход, получение токена |
| GET | /api/v1/users/me | User | Профиль текущего юзера |
| GET | /api/v1/halls/ | Public | Список активных залов |
| POST | /api/v1/halls/ | Admin | Создать зал |
| PATCH | /api/v1/halls/{id} | Admin | Обновить зал |
| DELETE | /api/v1/halls/{id} | Admin | Удалить зал |
| GET | /api/v1/halls/{id}/seats/ | Public | Места в зале |
| POST | /api/v1/halls/{id}/seats/ | Admin | Создать место |
| POST | /api/v1/halls/{id}/seats/bulk | Admin | Bulk создание мест |
| DELETE | /api/v1/halls/{id}/seats/{seat_id} | Admin | Удалить место |
| GET | /api/v1/bookings/ | User | Мои бронирования |
| GET | /api/v1/bookings/{id} | User | Детали бронирования |
| POST | /api/v1/bookings/ | User | Создать бронирование |
| DELETE | /api/v1/bookings/{id} | User | Отменить бронирование |
| GET | /api/v1/bookings/halls/{id}/availability | Public | Доступные слоты |

Документация (Swagger): **http://localhost:8000/docs**

---

## Конфигурация

### Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/booking_db` | Строка подключения к БД |
| `REDIS_URL` | `redis://localhost:6379/0` | URL Redis |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `JWT_SECRET_KEY` | `change-me-in-production` | Секрет для JWT |
| `JWT_ALGORITHM` | `HS256` | Алгоритм токена |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Время жизни токена |
| `SMTP_HOST` | - | SMTP сервер |
| `SMTP_PORT` | `587` | SMTP порт |
| `SMTP_USER` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password |

Для Docker значения подставляются через `docker-compose.yml`.

---

## Лицензия

MIT License — свободное использование для любых целей.

Подробности в файле [LICENSE](LICENSE).