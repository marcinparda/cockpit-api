from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.redis_store import services
from src.services.redis_store.dependencies import get_redis_client
from src.services.redis_store.schemas import StoreEnvelope, StoreKeyCreate, StoreKeyPatch

router = APIRouter(tags=["store"])


@router.get("/resolve/{prefix}/{category}/{key}", response_model=StoreEnvelope)
async def resolve_key(
    prefix: str,
    category: str,
    key: str,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.READ)),
) -> StoreEnvelope:
    return await services.resolve_key(client, prefix, category, key)


@router.get("/{prefix}/{category}", response_model=list[str])
async def list_keys(
    prefix: str,
    category: str,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.READ)),
) -> list[str]:
    return await services.list_keys(client, prefix, category)


@router.get("/{prefix}/{category}/{key}", response_model=StoreEnvelope)
async def get_key(
    prefix: str,
    category: str,
    key: str,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.READ)),
) -> StoreEnvelope:
    return await services.get_key(client, prefix, category, key)


@router.put("/{prefix}/{category}/{key}", response_model=StoreEnvelope)
async def put_key(
    prefix: str,
    category: str,
    key: str,
    body: StoreKeyCreate,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.UPDATE)),
) -> StoreEnvelope:
    return await services.put_key(client, prefix, category, key, body)


@router.patch("/{prefix}/{category}/{key}", response_model=StoreEnvelope)
async def patch_key(
    prefix: str,
    category: str,
    key: str,
    body: StoreKeyPatch,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.UPDATE)),
) -> StoreEnvelope:
    return await services.patch_key(client, prefix, category, key, body)


@router.delete("/{prefix}/{category}/{key}", status_code=204)
async def delete_key(
    prefix: str,
    category: str,
    key: str,
    client: Redis = Depends(get_redis_client),
    _: object = Depends(require_permission(Features.REDIS_STORE, Actions.DELETE)),
) -> None:
    await services.delete_key(client, prefix, category, key)
