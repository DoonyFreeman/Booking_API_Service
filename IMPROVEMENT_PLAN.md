# План улучшений для мидл-позиции

## Цель

Довести проект до уровня, который оценят на позицию **мидл-разработчика**.

**Текущий уровень:** Хороший пет-проект (базовый CRUD, авторизация, бизнес-логика)
**Целевой уровень:** Production-ready проект с защитой, тестами и observability

---

## Текущее состояние

| Критерий | Состояние |
|----------|-----------|
| Покрытие тестами | 59% |
| Rate Limiting | ❌ Нет |
| Graceful Shutdown | ❌ Нет |
| OpenAPI документация | Базованя |
| Логирование | Минимальное |

---

## Список улучшений

### 1. Rate Limiting
**Приоритет:** 🔴 Высокий
**Время:** 1-2 часа

**Цель:** Защита API от злоупотреблений и DDoS

**Что сделать:**
1. Добавить `slowapi` в зависимости
2. Настроить rate limits:
   - `/api/v1/auth/*` — 5 запросов/минуту (защита от брутфорса)
   - `/api/v1/bookings/*` — 10 запросов/минуту
   - `/api/v1/halls/*` — 30 запросов/минуту
   - `/api/v1/users/*` — 20 запросов/минуту

**Файлы:**
- `pyproject.toml` — добавить slowapi
- `app/main.py` — настроить limiter
- `app/routers/auth.py` — применить @limiter.limit
- `app/routers/bookings.py` — применить @limiter.limit

**Проверка:**
```bash
pytest tests/ -v
```

---

### 2. Тесты (59% → 70%+)
**Приоритет:** 🔴 Высокий
**Время:** 3-4 часа

**Цель:** Увеличить покрытие до 70%+ для уверенности в коде

**Текущее покрытие:**
```
auth_service.py      — 45%  (+15% нужно)
booking_service.py   — 36%  (+34% нужно)
seat_service.py      — 31%  (+39% нужно)
user_service.py      — 29%  (+41% нужно)
```

**Что сделать:**

#### 2.1. Тесты для `auth_service.py`
- Тест на валидацию email (некорректный формат)
- Тест на дублирующийся email
- Тест на короткий пароль

#### 2.2. Тесты для `booking_service.py`
- Тест на конфликт бронирования (занятое время)
- Тест на невалидное время (end < start)
- Тест на бронирование прошлого времени
- Тест на слишком длительное бронирование
- Тест на валидацию seat_ids (несуществующие)

#### 2.3. Тесты для `seat_service.py`
- Тест на дублирующееся место
- Тест на несуществующий hall
- Тест на bulk_create с конфликтом

#### 2.4. Тесты для `user_service.py`
- Тест на обновление несуществующего пользователя
- Тест на пагинацию

**Файлы:**
- `tests/test_auth_service.py` — создать
- `tests/test_booking_service.py` — создать
- `tests/test_seat_service.py` — создать
- `tests/test_user_service.py` — создать

**Проверка:**
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

**Цель:** TOTAL > 70%

---

### 3. Graceful Shutdown
**Приоритет:** 🟡 Средний
**Время:** 30 минут

**Цель:** Корректное завершение соединений при остановке контейнера

**Что сделать:**
1. Обновить `Dockerfile` — добавить STOPSIGNAL
2. Убедиться что shutdown handlers работают в `main.py`

**Файлы:**
- `Dockerfile`
- `app/main.py`

**Проверка:**
```bash
docker-compose up -d
docker-compose stop
# Проверить что нет zombie процессов
```

---

### 4. OpenAPI аннотации
**Приоритет:** 🟡 Средний
**Время:** 1 час

**Цель:** Улучшить Swagger документацию

**Что сделать:**
Добавить descriptions к endpoints:
```python
@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать бронирование",
    description="Создает новое бронирование для указанных мест и времени"
)
async def create_booking(...):
```

**Файлы:**
- `app/routers/auth.py`
- `app/routers/users.py`
- `app/routers/halls.py`
- `app/routers/seats.py`
- `app/routers/bookings.py`

**Проверка:**
```bash
# Открыть http://localhost:8000/docs и проверить описания
```

---

### 5. Логирование запросов
**Приоритет:** 🟢 Низкий
**Время:** 30 минут

**Цель:** Базовая observability для отладки

**Что сделать:**
Добавить middleware для логирования:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

**Файлы:**
- `app/main.py`

**Проверка:**
```bash
uvicorn app.main:app --log-level debug
# Увидеть логи запросов
```

---

## Порядок выполнения

| # | Задача | Время | Итого |
|---|--------|-------|-------|
| 1 | Rate Limiting | 1-2 ч | 2 ч |
| 2 | Тесты | 3-4 ч | 6 ч |
| 3 | Graceful Shutdown | 30 мин | 6.5 ч |
| 4 | OpenAPI аннотации | 1 ч | 7.5 ч |
| 5 | Логирование | 30 мин | 8 ч |

**Общее время:** ~8 часов

---

## Чеклист выполнения

### Rate Limiting
- [x] Добавить slowapi в зависимости
- [x] Настроить limiter в main.py
- [x] Применить к роутерам
- [x] Тесты проходят

### Тесты (59% → 70%+)
- [ ] Создать tests/test_auth_service.py
- [ ] Создать tests/test_booking_service.py
- [ ] Создать tests/test_seat_service.py
- [ ] Создать tests/test_user_service.py
- [ ] Покрытие > 70%

### Graceful Shutdown
- [ ] Обновить Dockerfile
- [ ] Проверить shutdown handlers

### OpenAPI аннотации
- [ ] Добавить summary/description к auth endpoints
- [ ] Добавить summary/description к users endpoints
- [ ] Добавить summary/description к halls endpoints
- [ ] Добавить summary/description к seats endpoints
- [ ] Добавить summary/description к bookings endpoints

### Логирование
- [ ] Добавить request logging middleware

---

## Финальная проверка

```bash
# 1. Все тесты проходят
pytest tests/ -v

# 2. Покрытие > 70%
pytest tests/ --cov=app --cov-report=term-missing

# 3. Ruff проверка
ruff check .

# 4. Docker собирается
docker-compose build

# 5. API работает
docker-compose up -d
curl http://localhost:8000/health
docker-compose down
```

---

## Критерии завершения

- [ ] Все тесты проходят (30/30)
- [ ] Покрытие > 70%
- [ ] Rate Limiting работает
- [ ] Graceful Shutdown настроен
- [ ] Swagger документация полная
- [ ] Логирование запросов работает
- [ ] Docker образ собирается без ошибок
