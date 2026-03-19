from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from src.core.config import settings


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    client: Redis = Redis.from_url(settings.REDIS_STORE_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
