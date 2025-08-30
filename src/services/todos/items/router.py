from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.users.models import User
from src.services.todos.items.schemas import (
    TodoItem,
    TodoItemCreate,
    TodoItemUpdate,
)
from src.services.authorization.permissions.enums import Actions
from src.services.todos.items.dependencies import get_todo_items_permissions
from src.services.authentication.dependencies import get_current_user
from src.services.todos.items.dependencies import (
    can_access_item,
)
from src.services.todos.items.models import TodoItem as TodoItemModel
from src.services.todos.items import service as todo_item_service
from src.services.todos.projects.service import can_user_access_project
from uuid import UUID


router = APIRouter()


@router.get("", response_model=List[TodoItem])
async def get_todo_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    sort_by: str = Query(
        "name", description="Field to sort by: id, name, created_at, updated_at, is_closed, completed_at"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """Retrieve todo items from projects the user has access to."""

    items = await todo_item_service.list_items_for_user_projects(
        db, current_user.id, skip=skip, limit=limit, sort_by=sort_by, order=order
    )

    return items


@router.post("", response_model=TodoItem, status_code=status.HTTP_201_CREATED)
async def create_todo_item(
    item: TodoItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(get_todo_items_permissions(Actions.CREATE)),
):
    """Create a new todo item in a project."""

    has_access = await can_user_access_project(
        db, item.project_id, UUID(str(current_user.id))
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    db_item = await todo_item_service.create_item(
        db,
        name=item.name,
        project_id=item.project_id,
        description=item.description,
        shops=item.shops,
        is_closed=False,
    )

    return await todo_item_service.get_item_by_id(db, db_item.id)


@router.get("/{item_id}", response_model=TodoItem)
async def get_todo_item(
    *,
    item: TodoItemModel = Depends(can_access_item),
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """Get todo item by ID if the user has access to its project."""

    return item


@router.put("/{item_id}", response_model=TodoItem)
async def update_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: TodoItemUpdate,
    item: TodoItemModel = Depends(can_access_item),
    _: None = Depends(get_todo_items_permissions(Actions.UPDATE))
) -> Any:
    """Update a todo item if the user has access to its project."""

    update_data = item_in.model_dump(exclude_unset=True)
    updated = await todo_item_service.update_item(db, item.id, **update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item.id} not found"
        )

    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item: TodoItemModel = Depends(can_access_item),
    _: None = Depends(get_todo_items_permissions(Actions.DELETE))
) -> Any:
    """Delete a todo item if the user has access to its project."""

    deleted = await todo_item_service.delete_item(db, item.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item.id} not found"
        )

    return deleted
