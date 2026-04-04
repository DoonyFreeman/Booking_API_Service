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
