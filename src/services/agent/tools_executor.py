import json
from datetime import date
from typing import Any

import httpx
from redis.asyncio import Redis

from src.core.config import settings
from src.services.actual_budget.client import make_actual_client
from src.services.agent.tools import CV_SECTIONS
from src.services.redis_store import repository as redis_repo
from src.services.redis_store.schemas import StoreEnvelope, StoreKeyCreate
from src.services.vikunja.client import get_vikunja_token, make_vikunja_client


def _budget_path(path: str) -> str:
    return f"/v1/budgets/{settings.ACTUAL_BUDGET_SYNC_ID}{path}"


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
                if isinstance(item, dict)
                else item
                for item in items
            ]
        elif key in ("skills", "achievements", "education"):
            result[key] = data if isinstance(data, list) else []
        else:
            result[key] = data
    return result


async def execute_tool(name: str, args: dict[str, Any], redis_client: Redis) -> Any:
    # CV tools
    if name == "search_company":
        return await _search_company(args["query"])
    if name == "get_cv_base_preset":
        return await _get_cv_base_preset(redis_client)
    if name == "create_cv_preset":
        return _build_confirm_required(args["name"], args["sections"])

    # Actual Budget tools
    if name == "actual_list_accounts":
        return await _actual_list_accounts()
    if name == "actual_create_account":
        return await _actual_create_account(args["name"], args["offbudget"])
    if name == "actual_list_categories":
        return await _actual_list_categories()
    if name == "actual_list_payees":
        return await _actual_list_payees()
    if name == "actual_search_transactions":
        return await _actual_search_transactions(args)
    if name == "actual_create_transaction":
        return await _actual_create_transaction(args)
    if name == "actual_batch_create_transactions":
        return await _actual_batch_create_transactions(args)
    if name == "actual_update_transaction":
        return await _actual_update_transaction(args)
    if name == "actual_delete_transaction":
        return await _actual_delete_transaction(args["transaction_id"])

    # Vikunja tools
    if name == "vikunja_list_projects":
        return await _vikunja_list_projects()
    if name == "vikunja_get_tasks":
        return await _vikunja_get_tasks(args)
    if name == "vikunja_create_task":
        return await _vikunja_create_task(args)
    if name == "vikunja_update_task":
        return await _vikunja_update_task(args)
    if name == "vikunja_delete_task":
        return await _vikunja_delete_task(args["task_id"])
    if name == "vikunja_list_users":
        return await _vikunja_list_users(args.get("s"))
    if name == "vikunja_assign_user_to_task":
        return await _vikunja_assign_user_to_task(args["task_id"], args["user_id"])
    if name == "vikunja_remove_assignee":
        return await _vikunja_remove_assignee(args["task_id"], args["user_id"])

    raise ValueError(f"Unknown tool: {name}")


async def write_cv_preset(name: str, sections: dict[str, Any], redis_client: Redis) -> None:
    preset_id = _name_to_id(name)
    sections = _sanitize_sections(sections)

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
        "sections": _sanitize_sections(sections),
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


# ── Actual Budget helpers ──────────────────────────────────────────────────────

async def _actual_list_accounts() -> Any:
    async with make_actual_client() as c:
        resp = await c.get(_budget_path("/accounts"))
        resp.raise_for_status()
        return resp.json()


async def _actual_create_account(name: str, offbudget: bool) -> Any:
    async with make_actual_client() as c:
        resp = await c.post(
            _budget_path("/accounts"),
            json={"account": {"name": name, "offbudget": offbudget}},
        )
        resp.raise_for_status()
        return resp.json()


async def _actual_list_categories() -> Any:
    async with make_actual_client() as c:
        resp = await c.get(_budget_path("/categories"))
        resp.raise_for_status()
        return resp.json()


async def _actual_list_payees() -> Any:
    async with make_actual_client() as c:
        resp = await c.get(_budget_path("/payees"))
        resp.raise_for_status()
        return resp.json()


async def _actual_search_transactions(args: dict[str, Any]) -> Any:
    account_id = args["account_id"]
    params: dict[str, Any] = {"since_date": args["since_date"]}
    if args.get("until_date"):
        params["until_date"] = args["until_date"]
    async with make_actual_client() as c:
        resp = await c.get(_budget_path(f"/accounts/{account_id}/transactions"), params=params)
        resp.raise_for_status()
        return resp.json()


async def _actual_create_transaction(args: dict[str, Any]) -> Any:
    account_id = args["account_id"]
    transaction: dict[str, Any] = {"date": args["date"], "amount": args["amount"]}
    if args.get("payee_name"):
        transaction["payee_name"] = args["payee_name"]
    if args.get("category_id"):
        transaction["category"] = args["category_id"]
    if args.get("notes"):
        transaction["notes"] = args["notes"]
    if args.get("cleared") is not None:
        transaction["cleared"] = args["cleared"]
    async with make_actual_client() as c:
        resp = await c.post(
            _budget_path(f"/accounts/{account_id}/transactions"),
            json={"transaction": transaction},
        )
        resp.raise_for_status()
        return resp.json()


async def _actual_batch_create_transactions(args: dict[str, Any]) -> Any:
    account_id = args["account_id"]
    transactions = []
    for t in args["transactions"]:
        tx: dict[str, Any] = {"date": t["date"], "amount": t["amount"]}
        if t.get("payee_name"):
            tx["payee_name"] = t["payee_name"]
        if t.get("category_id"):
            tx["category"] = t["category_id"]
        if t.get("notes"):
            tx["notes"] = t["notes"]
        transactions.append(tx)
    learn = args.get("learn_categories", True)
    async with make_actual_client() as c:
        resp = await c.post(
            _budget_path(f"/accounts/{account_id}/transactions/batch"),
            json={"transactions": transactions, "learnCategories": learn},
        )
        resp.raise_for_status()
        return resp.json()


async def _actual_update_transaction(args: dict[str, Any]) -> Any:
    transaction_id = args["transaction_id"]
    field_map = {
        "category_id": "category",
        "payee_name": "payee_name",
        "notes": "notes",
        "cleared": "cleared",
        "date": "date",
        "amount": "amount",
    }
    transaction: dict[str, Any] = {}
    for arg_key, tx_key in field_map.items():
        if args.get(arg_key) is not None:
            transaction[tx_key] = args[arg_key]
    async with make_actual_client() as c:
        resp = await c.patch(
            _budget_path(f"/transactions/{transaction_id}"),
            json={"transaction": transaction},
        )
        resp.raise_for_status()
        return resp.json()


async def _actual_delete_transaction(transaction_id: str) -> Any:
    async with make_actual_client() as c:
        resp = await c.delete(_budget_path(f"/transactions/{transaction_id}"))
        resp.raise_for_status()
        return {"success": True, "transaction_id": transaction_id}


# ── Vikunja helpers ────────────────────────────────────────────────────────────

async def _vikunja_list_projects() -> Any:
    token = await get_vikunja_token()
    async with make_vikunja_client(token) as c:
        resp = await c.get("/projects")
        resp.raise_for_status()
        return resp.json()


async def _vikunja_get_tasks(args: dict[str, Any]) -> Any:
    token = await get_vikunja_token()
    params: dict[str, Any] = {}
    for key in ("filter", "s", "sort_by", "order_by", "page", "per_page"):
        if args.get(key) is not None:
            params[key] = args[key]
    async with make_vikunja_client(token) as c:
        try:
            if args.get("project_id") is not None:
                resp = await c.get(f"/projects/{args['project_id']}/tasks", params=params)
            else:
                resp = await c.get("/tasks", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"Vikunja API error {e.response.status_code}", "detail": str(e)}


async def _vikunja_create_task(args: dict[str, Any]) -> Any:
    token = await get_vikunja_token()
    project_id = args["project_id"]
    task: dict[str, Any] = {"title": args["title"]}
    if args.get("description"):
        task["description"] = args["description"]
    if args.get("due_date"):
        task["due_date"] = args["due_date"]
    if args.get("priority") is not None:
        task["priority"] = args["priority"]
    if args.get("assignees"):
        task["assignees"] = [{"id": uid} for uid in args["assignees"]]
    async with make_vikunja_client(token) as c:
        resp = await c.put(f"/projects/{project_id}/tasks", json=task)
        resp.raise_for_status()
        return resp.json()


async def _vikunja_update_task(args: dict[str, Any]) -> Any:
    token = await get_vikunja_token()
    task_id = args["task_id"]
    task: dict[str, Any] = {}
    for key in ("title", "description", "done", "due_date", "priority"):
        if args.get(key) is not None:
            task[key] = args[key]
    async with make_vikunja_client(token) as c:
        resp = await c.post(f"/tasks/{task_id}", json=task)
        resp.raise_for_status()
        return resp.json()


async def _vikunja_delete_task(task_id: int) -> Any:
    token = await get_vikunja_token()
    async with make_vikunja_client(token) as c:
        resp = await c.delete(f"/tasks/{task_id}")
        resp.raise_for_status()
        return {"success": True, "task_id": task_id}


async def _vikunja_list_users(s: str | None = None) -> Any:
    token = await get_vikunja_token()
    params: dict[str, Any] = {}
    if s:
        params["s"] = s
    async with make_vikunja_client(token) as c:
        resp = await c.get("/users", params=params)
        resp.raise_for_status()
        return resp.json()


async def _vikunja_assign_user_to_task(task_id: int, user_id: int) -> Any:
    token = await get_vikunja_token()
    async with make_vikunja_client(token) as c:
        resp = await c.put(f"/tasks/{task_id}/assignees", json={"user_id": user_id})
        resp.raise_for_status()
        return resp.json()


async def _vikunja_remove_assignee(task_id: int, user_id: int) -> Any:
    token = await get_vikunja_token()
    async with make_vikunja_client(token) as c:
        resp = await c.delete(f"/tasks/{task_id}/assignees/{user_id}")
        resp.raise_for_status()
        return {"success": True, "task_id": task_id, "user_id": user_id}
