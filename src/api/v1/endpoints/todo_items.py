from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, asc

from src.core.database import get_db
from src.models.todo_item import TodoItem
from src.models.todo_project import TodoProject
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
    sort_by: str = Query(
        "name", description="Field to sort by: id, name, created_at, updated_at, is_closed, completed_at"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """
    Retrieve all todo items.
    """
    allowed_sort_fields = {"id", "name", "created_at",
                           "updated_at", "is_closed", "completed_at"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by field: {sort_by}")
    order_func = desc if order.lower() == "desc" else asc
    sort_column = getattr(TodoItem, sort_by)
    result = await db.execute(
        select(TodoItem)
        .options(selectinload(TodoItem.project))
        .order_by(order_func(sort_column))
        .offset(skip)
        .limit(limit)
    )
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
    project = None
    if item_in.project_id:
        project = await db.get(TodoProject, item_in.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    db_item = TodoItem(
        name=item_in.name,
        description=item_in.description,
        is_closed=False,
        shops=item_in.shops,
        project=project
    )
    db.add(db_item)
    await db.commit()
    # Eagerly load the project relationship after creation
    await db.refresh(db_item, attribute_names=["project"])
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
    item = await db.get(TodoItem, item_id, options=[selectinload(TodoItem.project)])
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
    db_item = await db.get(TodoItem, item_id, options=[selectinload(TodoItem.project)])
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )
    update_data = item_in.dict(exclude_unset=True)
    if "project_id" in update_data:
        if update_data["project_id"] is not None:
            project = await db.get(TodoProject, update_data["project_id"])
            if not project:
                raise HTTPException(
                    status_code=404, detail="Project not found")
            db_item.project = project
        else:
            db_item.project = None
        del update_data["project_id"]
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db_item.updated_at = datetime.utcnow()
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
