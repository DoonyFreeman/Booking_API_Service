from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis

from app.config import settings

redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> redis.Redis:
    if redis_client is None:
        return await init_redis()
    return redis_client


LOCK_PREFIX = "lock:booking:"


async def acquire_lock(
    client: redis.Redis,
    hall_id: int,
    date_str: str,
    timeout: int | None = None,
) -> bool:
    key = f"{LOCK_PREFIX}{hall_id}:{date_str}"
    timeout = timeout or settings.REDIS_LOCK_TIMEOUT
    return await client.set(key, "1", nx=True, ex=timeout)


async def release_lock(client: redis.Redis, hall_id: int, date_str: str) -> None:
    key = f"{LOCK_PREFIX}{hall_id}:{date_str}"
    await client.delete(key)
