from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.database import get_db
from src.models.shopping_item import ShoppingItem
from src.schemas.shopping_item import (
    ShoppingItem as ShoppingItemSchema,
    ShoppingItemCreate,
    ShoppingItemUpdate,
)

router = APIRouter()


@router.get("/items", response_model=List[ShoppingItemSchema])
async def get_shopping_items(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all shopping items.
    """
    result = await db.execute(select(ShoppingItem).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/items", response_model=ShoppingItemSchema, status_code=status.HTTP_201_CREATED)
async def create_shopping_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: ShoppingItemCreate,
) -> Any:
    """
    Create new shopping item.
    """
    db_item = ShoppingItem(
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


@router.get("/items/{item_id}", response_model=ShoppingItemSchema)
async def get_shopping_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> Any:
    """
    Get shopping item by ID.
    """
    item = await db.get(ShoppingItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping item with ID {item_id} not found"
        )
    return item


@router.put("/items/{item_id}", response_model=ShoppingItemSchema)
async def update_shopping_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    item_in: ShoppingItemUpdate,
) -> Any:
    """
    Update a shopping item.
    """
    db_item = await db.get(ShoppingItem, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping item with ID {item_id} not found"
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


@router.delete("/items/{item_id}", response_model=ShoppingItemSchema)
async def delete_shopping_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> Any:
    """
    Delete a shopping item.
    """
    db_item = await db.get(ShoppingItem, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping item with ID {item_id} not found"
        )

    await db.delete(db_item)
    await db.commit()
    return db_item
