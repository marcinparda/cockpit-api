from fastapi import APIRouter, Depends, HTTPException

import httpx

from src.services.authentication.dependencies import get_current_user
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.users.models import User
from src.services.vikunja import client
from src.services.vikunja.schemas import CreateTaskRequest, UpdateTaskRequest

router = APIRouter(tags=["vikunja"])


async def _get_token() -> str:
    try:
        return await client.get_vikunja_token()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Vikunja auth failed: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Vikunja unreachable")


@router.get("/projects")
async def list_projects(
    _: User = Depends(require_permission(Features.VIKUNJA, Actions.READ)),
):
    token = await _get_token()
    try:
        async with client.make_vikunja_client(token) as c:
            resp = await c.get("/projects")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Vikunja request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Vikunja unreachable")


@router.get("/projects/{project_id}/tasks")
async def list_tasks(
    project_id: int,
    _: User = Depends(require_permission(Features.VIKUNJA, Actions.READ)),
):
    token = await _get_token()
    try:
        async with client.make_vikunja_client(token) as c:
            resp = await c.get(f"/projects/{project_id}/tasks")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Vikunja request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Vikunja unreachable")


@router.post("/tasks", status_code=201)
async def create_task(
    body: CreateTaskRequest,
    _: User = Depends(require_permission(Features.VIKUNJA, Actions.CREATE)),
):
    token = await _get_token()
    try:
        async with client.make_vikunja_client(token) as c:
            resp = await c.put(f"/projects/{body.project_id}/tasks", json=body.model_dump(exclude_none=True))
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Vikunja request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Vikunja unreachable")


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    body: UpdateTaskRequest,
    _: User = Depends(require_permission(Features.VIKUNJA, Actions.UPDATE)),
):
    token = await _get_token()
    try:
        async with client.make_vikunja_client(token) as c:
            resp = await c.post(f"/tasks/{task_id}", json=body.model_dump(exclude_none=True))
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Vikunja request failed")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Vikunja unreachable")
