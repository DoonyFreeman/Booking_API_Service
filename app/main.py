import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import create_tables
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
from app.kafka import close_kafka, init_kafka
from app.redis import close_redis, init_redis
from app.routers import auth, bookings, halls, seats, users

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    return app


app = create_app()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
