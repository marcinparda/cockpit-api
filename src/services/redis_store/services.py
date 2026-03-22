from datetime import datetime, timezone

from fastapi import HTTPException, status
from redis.asyncio import Redis

from src.services.redis_store import repository
from src.services.redis_store.schemas import StoreEnvelope, StoreKeyCreate, StoreKeyPatch, StoreMeta


def _build_redis_key(prefix: str, category: str, key: str) -> str:
    return f"{prefix}:{category}:{key}"


async def get_key(client: Redis, prefix: str, category: str, key: str) -> StoreEnvelope:
    redis_key = _build_redis_key(prefix, category, key)
    envelope = await repository.get_key(client, redis_key)
    if envelope is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Key '{redis_key}' not found")
    return envelope


async def put_key(
    client: Redis, prefix: str, category: str, key: str, body: StoreKeyCreate
) -> StoreEnvelope:
    redis_key = _build_redis_key(prefix, category, key)
    now = datetime.now(timezone.utc)

    existing = await repository.get_key(client, redis_key)
    version = (existing.meta.version + 1) if existing else 1
    created_at = existing.meta.created_at if existing else now

    envelope = StoreEnvelope(
        meta=StoreMeta(
            key=redis_key,
            type=body.type,
            version=version,
            created_at=created_at,
            updated_at=now,
            tags=body.tags,
        ),
        data=body.data,
    )
    await repository.set_key(client, redis_key, envelope)
    return envelope


async def patch_key(
    client: Redis, prefix: str, category: str, key: str, body: StoreKeyPatch
) -> StoreEnvelope:
    redis_key = _build_redis_key(prefix, category, key)
    existing = await repository.get_key(client, redis_key)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Key '{redis_key}' not found")

    if isinstance(existing.data, dict):
        merged_data = {**existing.data, **body.data}
    else:
        merged_data = body.data

    updated = StoreEnvelope(
        meta=StoreMeta(
            key=redis_key,
            type=existing.meta.type,
            version=existing.meta.version + 1,
            created_at=existing.meta.created_at,
            updated_at=datetime.now(timezone.utc),
            tags=existing.meta.tags,
        ),
        data=merged_data,
    )
    await repository.set_key(client, redis_key, updated)
    return updated


async def delete_key(client: Redis, prefix: str, category: str, key: str) -> None:
    redis_key = _build_redis_key(prefix, category, key)
    deleted = await repository.delete_key(client, redis_key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Key '{redis_key}' not found")


async def list_keys(client: Redis, prefix: str, category: str) -> list[str]:
    pattern = _build_redis_key(prefix, category, "*")
    return await repository.list_keys(client, pattern)


async def list_prefixes(client: Redis) -> list[str]:
    keys = await repository.list_all_keys(client)
    return sorted({k.split(":")[0] for k in keys})


async def list_categories(client: Redis, prefix: str) -> list[str]:
    keys = await repository.list_keys(client, f"{prefix}:*:*")
    return sorted({k.split(":")[1] for k in keys})


async def resolve_key(client: Redis, prefix: str, category: str, key: str) -> StoreEnvelope:
    base_redis_key = _build_redis_key("base", category, key)
    base = await repository.get_key(client, base_redis_key)
    if base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Base key '{base_redis_key}' not found")

    if prefix == "base":
        return base

    override_redis_key = _build_redis_key(prefix, category, key)
    override = await repository.get_key(client, override_redis_key)
    if override is None:
        return base

    # Shallow merge: dicts merge, arrays/scalars are fully replaced by override
    if isinstance(base.data, dict) and isinstance(override.data, dict):
        merged_data = {**base.data, **override.data}
    else:
        merged_data = override.data

    return StoreEnvelope(meta=base.meta, data=merged_data)
