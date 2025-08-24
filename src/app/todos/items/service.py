from __future__ import annotations

from typing import List, Sequence, Optional
from datetime import datetime
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.todos.items import repository as repository
from src.app.todos.items.models import TodoItem as TodoItemModel
from src.services.todo_access_service import get_accessible_project_ids


async def list_items_by_project(db: AsyncSession, project_id: int) -> List[TodoItemModel]:
    """Return all items for a given project."""
    return await repository.list_items_by_project(db, project_id)


async def list_items_for_user_projects(
    db: AsyncSession,
    user_id,
    skip: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    order: str = "asc",
) -> List[TodoItemModel]:
    """Return items for projects the user has access to with pagination and sorting.

    user_id can be a UUID or a string convertible to UUID; service just passes it to access helper.
    """
    project_ids = await get_accessible_project_ids(db, user_id)
    if not project_ids:
        return []

    order_by = None
    if sort_by:
        # Validate attribute exists on model
        if not hasattr(TodoItemModel, sort_by):
            raise ValueError(f"Invalid sort field: {sort_by}")
        sort_attr = getattr(TodoItemModel, sort_by)
        order_func = asc if order == "asc" else desc
        order_by = order_func(sort_attr)

    return await repository.list_items_by_project_ids(
        db, project_ids, skip=skip, limit=limit, order_by=order_by
    )


async def get_item_by_id(db: AsyncSession, item_id: int) -> Optional[TodoItemModel]:
    """Get a single item by id."""
    return await repository.get_item_by_id(db, item_id)


async def create_item(
    db: AsyncSession,
    *,
    name: str,
    project_id: int,
    description: Optional[str] = None,
    shops: Optional[str] = None,
    is_closed: bool = False,
) -> TodoItemModel:
    """Create a new todo item."""
    return await repository.create_item(
        db,
        name=name,
        project_id=project_id,
        description=description,
        shops=shops,
        is_closed=is_closed,
    )


async def update_item(db: AsyncSession, item_id: int, **fields) -> Optional[TodoItemModel]:
    """Update an item and return the updated object or None if not found."""
    return await repository.update_item(db, item_id, **fields)


async def delete_item(db: AsyncSession, item_id: int) -> Optional[TodoItemModel]:
    """Delete an item and return the deleted object or None if not found."""
    return await repository.delete_item(db, item_id)
