from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "Booking API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/booking_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_LOCK_TIMEOUT: int = 10

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_BOOKING_EVENTS: str = "booking-events"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@booking.api"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Booking limits
    MIN_BOOKING_HOURS: int = 1
    MAX_BOOKING_HOURS: int = 8
    SESSION_START_HOUR: int = 9
    SESSION_END_HOUR: int = 23


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
