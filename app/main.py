import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import create_tables
from app.kafka import close_kafka, init_kafka
from app.redis import close_redis, init_redis
from app.routers import auth

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

    return app


app = create_app()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
