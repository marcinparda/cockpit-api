from redis.asyncio import Redis

from src.services.redis_store.schemas import StoreEnvelope


async def get_key(client: Redis, redis_key: str) -> StoreEnvelope | None:
    result = await client.json().get(redis_key, "$")
    if not result:
        return None
    return StoreEnvelope(**result[0])


async def set_key(client: Redis, redis_key: str, envelope: StoreEnvelope) -> None:
    await client.json().set(redis_key, "$", envelope.model_dump(mode="json"))


async def delete_key(client: Redis, redis_key: str) -> bool:
    result = await client.json().delete(redis_key, "$")
    return bool(result)


async def list_keys(client: Redis, pattern: str) -> list[str]:
    keys = await client.keys(pattern)
    return [k if isinstance(k, str) else k.decode() for k in keys]
