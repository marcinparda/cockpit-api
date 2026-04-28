from typing import Any

from mcp.server.fastmcp import FastMCP

CV_SECTIONS = ["header", "summary", "skills", "achievements", "experience", "education", "projects", "courses"]


def register_cv_tools(mcp: FastMCP) -> None:
    from src.core.config import settings

    def _get_redis():
        from src.services.mcp import server
        return server.redis_client

    @mcp.tool()
    async def search_company(query: str) -> Any:
        """Search the web for company culture, values, tech stack, and buzzwords to tailor CV language.

        Args:
            query: Search query, e.g. 'Stripe engineering culture values tech stack'
        """
        import httpx

        url = "https://google.serper.dev/search"
        headers = {"Content-Type": "application/json", "X-API-KEY": settings.SERPER_API_KEY}
        payload = {"q": query, "num": 5}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return {
            "results": [
                {"title": item.get("title", ""), "description": item.get("snippet", ""), "url": item.get("link", "")}
                for item in data.get("organic", [])
            ]
        }

    @mcp.tool()
    async def get_cv_base_preset() -> Any:
        """Read all sections from the user's base CV preset. Always read before tailoring."""
        from src.services.redis_store import repository as redis_repo

        redis_client = _get_redis()
        sections: dict[str, Any] = {}
        for section in CV_SECTIONS:
            redis_key = f"base:cv:{section}"
            envelope = await redis_repo.get_key(redis_client, redis_key)
            if envelope is not None:
                sections[section] = envelope.data
        return sections

    @mcp.tool()
    async def preview_cv_preset(name: str, sections: dict[str, Any]) -> Any:
        """Preview a tailored CV preset based on the job offer WITHOUT saving it.
        Call this first, show the result to the user, and ask for confirmation before calling save_cv_preset.

        Args:
            name: Preset name, e.g. 'Stripe - Senior Backend 2026-04-28'
            sections: CV sections dict. Omit sections to exclude them from this preset.
        """
        return {
            "preview": True,
            "preset_name": name,
            "sections": _sanitize_sections(sections),
            "message": "Review the preset above. Confirm to save with save_cv_preset.",
        }

    @mcp.tool()
    async def save_cv_preset(name: str, sections: dict[str, Any]) -> Any:
        """Save a CV preset to storage. Only call after the user has confirmed the preview from preview_cv_preset.

        Args:
            name: Preset name
            sections: CV sections dict to persist
        """
        from datetime import date
        from src.services.redis_store import repository as redis_repo
        from src.services.redis_store.schemas import StoreEnvelope, StoreKeyCreate, StoreMeta
        from datetime import datetime, timezone

        redis_client = _get_redis()
        preset_id = _name_to_id(name)
        sections = _sanitize_sections(sections)
        now = datetime.now(timezone.utc)

        for section_key, data in sections.items():
            if section_key not in CV_SECTIONS:
                continue
            redis_key = f"{preset_id}:cv:{section_key}"
            body = StoreKeyCreate(type="cv_section", tags=["cv", section_key], data=data)
            envelope = StoreEnvelope(
                meta=StoreMeta(key=redis_key, type=body.type, version=1, created_at=now, updated_at=now, tags=body.tags),
                data=data,
            )
            await redis_repo.set_key(redis_client, redis_key, envelope)

        registry_key = "registry:cv:presets"
        existing = await redis_repo.get_key(redis_client, registry_key)
        registry: list[dict] = existing.data if existing and isinstance(existing.data, list) else []
        if not any(p.get("id") == preset_id for p in registry):
            registry.append({"id": preset_id, "label": name, "created_at": date.today().isoformat(), "archived": False})
            body_reg = StoreKeyCreate(type="cv_registry", tags=["cv", "presets"], data=registry)
            envelope_reg = StoreEnvelope(
                meta=StoreMeta(key=registry_key, type=body_reg.type, version=1, created_at=now, updated_at=now, tags=body_reg.tags),
                data=registry,
            )
            await redis_repo.set_key(redis_client, registry_key, envelope_reg)

        return {"success": True, "preset_id": preset_id, "preset_name": name}


def _name_to_id(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")


def _coerce_str_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(item) for item in val if item is not None]
    if isinstance(val, str) and val.strip():
        return [val]
    return []


def _sanitize_sections(sections: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, data in sections.items():
        if key in ("summary", "courses"):
            result[key] = _coerce_str_list(data)
        elif key in ("experience", "projects"):
            items = data if isinstance(data, list) else []
            result[key] = [
                {**item, "description": _coerce_str_list(item.get("description", []))}
                if isinstance(item, dict) else item
                for item in items
            ]
        elif key in ("skills", "achievements", "education"):
            result[key] = data if isinstance(data, list) else []
        else:
            result[key] = data
    return result
