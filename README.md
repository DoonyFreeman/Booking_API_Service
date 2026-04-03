# Booking API Service

REST API для бронирования залов кинотеатра с местами.

## На текущий момент

### Реализовано

| Компонент | Описание |
|-----------|---------|
| Auth | Регистрация, авторизация (JWT) |
| Users | CRUD пользователей (admin) |
| Halls | CRUD залов (admin) |
| Seats | CRUD мест (admin, bulk создание) |
| Bookings | Создание, отмена, список бронирований |
| Availability | Проверка доступных слотов (с кешированием) |
| Kafka Worker | Обработка событий бронирования |
| Docker | API + Worker в контейнерах |

### В разработке

- Тесты (pytest)

## Tech Stack

FastAPI • PostgreSQL • Redis • Kafka • JWT • Docker

## Быстрый старт

### Запуск

```bash
docker-compose up --build
```

API будет доступен по адресу: http://localhost:8000/docs

### Создание администратора

```bash
docker exec booking_api python -m app.scripts.create_admin \
  --email admin@test.com \
  --password secret123
```

### Тестирование end-to-end

1. Зайдите в Swagger UI: http://localhost:8000/docs
2. Зарегистрируйтесь или войдите: POST /api/v1/auth/login
3. Нажмите **Authorize** (🔓) и вставьте токен **БЕЗ** префикса `Bearer `
4. Создайте зал: POST /api/v1/halls/
5. Создайте места: POST /api/v1/halls/1/seats/bulk
6. Создайте бронирование: POST /api/v1/bookings/
7. Проверьте Kafka: смотрите логи worker или консоль consumer

### Просмотр Kafka сообщений

```bash
docker exec booking_kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --topic booking-events --from-beginning --bootstrap-server localhost:9092
```

### Просмотр логов

```bash
docker-compose logs -f worker
docker-compose logs -f api
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/v1/auth/signup | Регистрация |
| POST | /api/v1/auth/login | Вход (JWT) |
| GET | /api/v1/users/me | Профиль |
| GET | /api/v1/halls/ | Список залов |
| POST | /api/v1/halls/ | Создать зал (admin) |
| GET | /api/v1/halls/{id}/seats/ | Места в зале |
| POST | /api/v1/halls/{id}/seats/bulk | Bulk создание мест |
| POST | /api/v1/bookings/ | Создать бронирование |
| GET | /api/v1/bookings/ | Мои бронирования |
| GET | /api/v1/bookings/halls/{id}/availability | Доступные слоты |

## Документация API

http://localhost:8000/docs

## Архитектура

```mermaid
graph TB
    subgraph API Layer
        R[Router] --> S[Service]
        S --> M[Models]
    end

    subgraph Infrastructure
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Kafka[(Kafka)]
        SMTP[Email SMTP]
    end

    R --> DB
    R --> Redis
    R --> Kafka
    R --> SMTP

    subgraph Workers
        W[Email Worker]
    end

    Kafka --> W
    W --> SMTP
```

## Flow бронирования

```mermaid
sequenceDiagram
    User->>API: POST /bookings
    API->>Auth: Validate JWT
    Auth-->>API: User OK
    API->>Redis: Acquire Lock
    Redis-->>API: Lock OK
    API->>DB: Check conflicts
    DB-->>API: No conflicts
    API->>DB: Create booking
    API->>Kafka: Send event
    API-->>User: 201 Created
    Kafka->>Worker: booking_created
    Worker->>SMTP: Send email
```

## Environment Variables

```bash
# Для локальной разработки (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/booking_db
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Для Docker (.env в compose)
# DATABASE_URL, REDIS_URL, KAFKA_BOOTSTRAP_SERVERS
# задаются через environment: в docker-compose.yml
# ВАЖНО: KAFKA_BOOTSTRAP_SERVERS=kafka:9092 (не localhost!)
```
