FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first for better caching
COPY pyproject.toml .

# Install all dependencies explicitly
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]" \
    "sqlalchemy[asyncio]" \
    asyncpg \
    aiosqlite \
    alembic \
    pydantic \
    pydantic-settings \
    "redis[hiredis]" \
    aiokafka \
    "python-jose[cryptography]" \
    passlib \
    "bcrypt==4.0.1" \
    aiosmtplib \
    email-validator \
    httpx \
    pytest \
    pytest-asyncio \
    pytest-cov \
    greenlet

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Expose port
EXPOSE 8000

# Set stop signal for graceful shutdown
STOPSIGNAL SIGTERM

# Health check for container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]