from __future__ import annotations

from datetime import datetime
from typing import List, Sequence, Optional

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.todos.items.models import TodoItem as TodoItemModel


async def list_items_by_project(db: AsyncSession, project_id: int) -> List[TodoItemModel]:
    """Return all items for a given project ordered by created_at desc."""
    res = await db.execute(
        select(TodoItemModel).where(TodoItemModel.project_id == project_id)
        .order_by(TodoItemModel.created_at.desc())
    )
    return list(res.scalars().all())


async def list_items_by_project_ids(
    db: AsyncSession,
    project_ids: Sequence[int],
    skip: int = 0,
    limit: int = 100,
    order_by=None,
) -> List[TodoItemModel]:
    """Return items for a list of project ids with pagination and optional ordering."""
    if not project_ids:
        return []

    stmt = select(TodoItemModel).options(selectinload(TodoItemModel.project)).where(
        TodoItemModel.project_id.in_(project_ids))
    if order_by is not None:
        stmt = stmt.order_by(order_by)

    stmt = stmt.offset(skip).limit(limit)

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_item_by_id(db: AsyncSession, item_id: int) -> Optional[TodoItemModel]:
    """Get a single item by its id or return None if not found."""
    stmt = select(TodoItemModel).options(selectinload(TodoItemModel.project)).where(TodoItemModel.id == item_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_item(
    db: AsyncSession,
    *,
    name: str,
    project_id: int,
    description: str | None = None,
    shops: str | None = None,
    is_closed: bool = False,
) -> TodoItemModel:
    """Create a new todo item using a Core insert and return the ORM row."""
    now = datetime.now()
    stmt = (
        insert(TodoItemModel)
        .values(
            name=name,
            project_id=project_id,
            description=description,
            shops=shops,
            is_closed=is_closed,
            created_at=now,
            updated_at=now,
        )
        .returning(TodoItemModel)
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.scalar_one()


async def update_item(db: AsyncSession, item_id: int, **fields) -> Optional[TodoItemModel]:
    """Update fields on an existing item and return the updated ORM object.

    Returns None if item does not exist.
    """
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    for key, value in fields.items():
        setattr(item, key, value)

    item.updated_at = datetime.now()
    await db.commit()
    await db.refresh(item, ["project"])  # Refresh with project relationship
    return item


async def delete_item(db: AsyncSession, item_id: int) -> Optional[TodoItemModel]:
    """Delete an item and return the deleted ORM object (or None if not found)."""
    item = await get_item_by_id(db, item_id)
    if not item:
        return None

    await db.delete(item)
    await db.commit()
    return item
