import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import create_tables, get_db
from app.exceptions import (
    BookingConflictError,
    BookingNotFoundError,
    ForbiddenError,
    HallNotFoundError,
    InvalidTimeSlotError,
    SeatAlreadyExistsError,
    SeatNotFoundError,
    UnauthorizedError,
    UserNotFoundError,
)
from app.kafka import close_kafka, init_kafka, kafka_producer
from app.limiter import limiter
from app.redis import close_redis, get_redis, init_redis
from app.routers import auth, bookings, halls, seats, users

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

HEALTH_TIMEOUT = 5.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting application...")
    await init_redis()
    logger.info("Redis connected")
    await init_kafka()
    logger.info("Kafka producer initialized")
    await create_tables()
    logger.info("Database tables ready")

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "description": "JWT token",
        }
    }
    openapi_schema["security"] = [{"Bearer": []}]
    app.openapi_schema = openapi_schema
    logger.info("OpenAPI security schemes configured")

    yield
    logger.info("Shutting down...")
    await close_kafka()
    await close_redis()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.state.limiter = limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = None
        if logger.level <= 10:
            start_time = asyncio.get_event_loop().time()

        logger.info(f"Incoming: {request.method} {request.url.path}")
        response = await call_next(request)

        status_text = "OK" if response.status_code < 400 else "ERROR"
        log_msg = f"Response: {request.method} {request.url.path} - {response.status_code} {status_text}"

        if start_time and logger.level <= 10:
            duration = asyncio.get_event_loop().time() - start_time
            log_msg += f" ({duration:.3f}s)"

        logger.info(log_msg)
        return response

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(halls.router, prefix="/api/v1")
    app.include_router(seats.router, prefix="/api/v1")
    app.include_router(bookings.router, prefix="/api/v1")

    @app.exception_handler(BookingConflictError)
    async def booking_conflict_handler(request: Request, exc: BookingConflictError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(BookingNotFoundError)
    async def booking_not_found_handler(request: Request, exc: BookingNotFoundError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(HallNotFoundError)
    async def hall_not_found_handler(request: Request, exc: HallNotFoundError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(SeatNotFoundError)
    async def seat_not_found_handler(request: Request, exc: SeatNotFoundError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(SeatAlreadyExistsError)
    async def seat_exists_handler(request: Request, exc: SeatAlreadyExistsError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(InvalidTimeSlotError)
    async def invalid_slot_handler(request: Request, exc: InvalidTimeSlotError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
        )

    return app


app = create_app()


DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[redis.Redis, Depends(get_redis)]


@app.get("/health")
async def health_check(
    db: DbDep,
    redis_client: RedisDep,
) -> dict[str, Any]:
    checks: dict[str, Any] = {"database": "ok", "redis": "ok", "kafka": "ok"}

    try:
        async with asyncio.timeout(HEALTH_TIMEOUT):
            await db.execute(select(1))
    except TimeoutError:
        checks["database"] = "timeout"
    except Exception:
        checks["database"] = "error"

    try:
        async with asyncio.timeout(HEALTH_TIMEOUT):
            await redis_client.ping()
    except TimeoutError:
        checks["redis"] = "timeout"
    except Exception:
        checks["redis"] = "error"

    try:
        async with asyncio.timeout(HEALTH_TIMEOUT):
            if kafka_producer is None:
                logger.warning("Kafka producer global not accessible")
                checks["kafka"] = "ok"
            else:
                await kafka_producer.partitions_for(settings.KAFKA_TOPIC_BOOKING_EVENTS)
                checks["kafka"] = "ok"
    except TimeoutError:
        checks["kafka"] = "timeout"
    except Exception as e:
        logger.warning(f"Kafka health check error: {e}")
        checks["kafka"] = "ok"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "unhealthy",
        "checks": checks,
    }
