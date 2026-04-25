import httpx
from redis.asyncio import Redis

from src.core.config import settings

_VIKUNJA_TOKEN_REDIS_KEY = "vikunja:auth_token"
_VIKUNJA_TOKEN_TTL = 3600


async def get_vikunja_token(redis_client: Redis | None = None) -> str:
    if redis_client is not None:
        cached = await redis_client.get(_VIKUNJA_TOKEN_REDIS_KEY)
        if cached:
            return cached if isinstance(cached, str) else cached.decode()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.VIKUNJA_BASE_URL}/login",
            json={"username": settings.VIKUNJA_USERNAME, "password": settings.VIKUNJA_PASSWORD},
        )
        resp.raise_for_status()
        token: str = resp.json()["token"]

    if redis_client is not None:
        await redis_client.set(_VIKUNJA_TOKEN_REDIS_KEY, token, ex=_VIKUNJA_TOKEN_TTL)

    return token


def make_vikunja_client(token: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.VIKUNJA_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
