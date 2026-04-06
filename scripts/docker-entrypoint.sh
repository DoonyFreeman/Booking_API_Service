#!/bin/bash
set -e

echo "Running Alembic migrations..."
# Use DATABASE_URL from environment for Alembic (replace prefix)
ALEMBIC_URL="${DATABASE_URL/postgresql+asyncpg/postgresql}"
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000