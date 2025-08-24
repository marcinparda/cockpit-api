from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from .schemas import Category, CategoryCreate, CategoryUpdate
from .service import (
    get_all_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category
)
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_categories_permissions

router = APIRouter()


@router.get("", response_model=list[Category])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    return await get_all_categories(db)


@router.post("", response_model=Category)
async def create_category_endpoint(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.CREATE))
):
    return await create_category(db, category_data)


@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=Category)
async def update_category_endpoint(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    category = await update_category(db, category_id, category_data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category_endpoint(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    deleted = await delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
