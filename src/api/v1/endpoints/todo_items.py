from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.models.todo_item import TodoItem
from src.schemas.todo_item import (
    TodoItem as TodoItemSchema,
    TodoItemCreate,
    TodoItemUpdate,
)
from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_todo_items_permissions

router = APIRouter()


@router.get("/", response_model=List[TodoItemSchema])
async def get_todo_items(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """
    Retrieve all todo items.
    """
    result = await db.execute(select(TodoItem).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=TodoItemSchema, status_code=status.HTTP_201_CREATED)
async def create_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: TodoItemCreate,
    _: None = Depends(get_todo_items_permissions(Actions.CREATE))
) -> Any:
    """
    Create new todo item.
    """
    db_item = TodoItem(
        name=item_in.name,
        description=item_in.description,
        is_closed=False,
        categories=item_in.categories,
        shops=item_in.shops
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/{item_id}", response_model=TodoItemSchema)
async def get_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """
    Get todo item by ID.
    """
    item = await db.get(TodoItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )
    return item


@router.put("/{item_id}", response_model=TodoItemSchema)
async def update_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    item_in: TodoItemUpdate,
    _: None = Depends(get_todo_items_permissions(Actions.UPDATE))
) -> Any:
    """
    Update a todo item.
    """
    db_item = await db.get(TodoItem, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    update_data = item_in.dict(exclude_unset=True)

    # If item is being closed and completed_at is not provided, set it to now
    if update_data.get("is_closed") and not update_data.get("completed_at"):
        update_data["completed_at"] = datetime.now()

    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", response_model=TodoItemSchema)
async def delete_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    _: None = Depends(get_todo_items_permissions(Actions.DELETE))
) -> Any:
    """
    Delete a todo item.
    """
    db_item = await db.get(TodoItem, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    await db.delete(db_item)
    await db.commit()
    return db_item
