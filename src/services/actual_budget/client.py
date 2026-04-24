import httpx

from src.core.config import settings


def make_actual_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.ACTUAL_HTTP_API_URL,
        headers={"X-Api-Key": settings.ACTUAL_HTTP_API_KEY},
        timeout=15.0,
    )
