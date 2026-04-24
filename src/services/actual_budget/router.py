from fastapi import APIRouter, Depends, HTTPException, Query

import httpx

from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.users.models import User
from src.core.config import settings
from src.services.actual_budget import client

router = APIRouter(tags=["actual_budget"])


def _budget_path(path: str) -> str:
    return f"/v1/budgets/{settings.ACTUAL_BUDGET_SYNC_ID}{path}"


@router.get("/accounts")
async def list_accounts(
    _: User = Depends(require_permission(Features.AGENT, Actions.READ)),
):
    try:
        async with client.make_actual_client() as c:
            resp = await c.get(_budget_path("/accounts"))
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Actual Budget request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Actual Budget unreachable")


@router.get("/transactions")
async def list_transactions(
    account_id: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    _: User = Depends(require_permission(Features.AGENT, Actions.READ)),
):
    params: dict = {}
    if account_id:
        params["accountId"] = account_id
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    try:
        async with client.make_actual_client() as c:
            resp = await c.get(_budget_path("/transactions"), params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Actual Budget request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Actual Budget unreachable")
