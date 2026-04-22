import json
from datetime import date
from typing import Any

import httpx
from redis.asyncio import Redis

from src.core.config import settings
from src.services.agent.tools import CV_SECTIONS
from src.services.redis_store import repository as redis_repo
from src.services.redis_store.schemas import StoreEnvelope, StoreKeyCreate


async def execute_tool(name: str, args: dict[str, Any], redis_client: Redis) -> Any:
    if name == "search_company":
        return await _search_company(args["query"])
    if name == "get_cv_base_preset":
        return await _get_cv_base_preset(redis_client)
    if name == "create_cv_preset":
        return _build_confirm_required(args["name"], args["sections"])
    raise ValueError(f"Unknown tool: {name}")


async def write_cv_preset(name: str, sections: dict[str, Any], redis_client: Redis) -> None:
    preset_id = _name_to_id(name)

    for section_key, data in sections.items():
        if section_key not in CV_SECTIONS:
            continue
        redis_key = f"{preset_id}:cv:{section_key}"
        body = StoreKeyCreate(type="cv_section", tags=["cv", section_key], data=data)
        envelope = StoreEnvelope(
            meta=_build_meta(redis_key, body),
            data=data,
        )
        await redis_repo.set_key(redis_client, redis_key, envelope)

    await _register_preset(preset_id, name, redis_client)


async def _search_company(query: str) -> dict[str, Any]:
    url = "https://google.serper.dev/search"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.SERPER_API_KEY,
    }
    payload = {"q": query, "num": 5}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "description": item.get("snippet", ""),
            "url": item.get("link", ""),
        })

    return {"results": results}


async def _get_cv_base_preset(redis_client: Redis) -> dict[str, Any]:
    sections: dict[str, Any] = {}
    for section in CV_SECTIONS:
        redis_key = f"base:cv:{section}"
        envelope = await redis_repo.get_key(redis_client, redis_key)
        if envelope is not None:
            sections[section] = envelope.data
    return sections


def _build_confirm_required(name: str, sections: dict[str, Any]) -> dict[str, Any]:
    return {
        "confirm_required": True,
        "preset_name": name,
        "sections": sections,
    }


async def _register_preset(preset_id: str, label: str, redis_client: Redis) -> None:
    registry_key = "registry:cv:presets"
    existing = await redis_repo.get_key(redis_client, registry_key)
    registry: list[dict] = existing.data if existing and isinstance(existing.data, list) else []

    if not any(p.get("id") == preset_id for p in registry):
        registry.append({
            "id": preset_id,
            "label": label,
            "created_at": date.today().isoformat(),
            "archived": False,
        })
        body = StoreKeyCreate(type="cv_registry", tags=["cv", "presets"], data=registry)
        envelope = StoreEnvelope(
            meta=_build_meta(registry_key, body),
            data=registry,
        )
        await redis_repo.set_key(redis_client, registry_key, envelope)


def _name_to_id(name: str) -> str:
    import re
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _build_meta(redis_key: str, body: StoreKeyCreate):
    from datetime import datetime, timezone
    from src.services.redis_store.schemas import StoreMeta
    now = datetime.now(timezone.utc)
    return StoreMeta(
        key=redis_key,
        type=body.type,
        version=1,
        created_at=now,
        updated_at=now,
        tags=body.tags,
    )
