import httpx

from src.core.config import settings


async def get_vikunja_token() -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.VIKUNJA_BASE_URL}/login",
            json={"username": settings.VIKUNJA_USERNAME, "password": settings.VIKUNJA_PASSWORD},
        )
        resp.raise_for_status()
        return resp.json()["token"]


def make_vikunja_client(token: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.VIKUNJA_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
