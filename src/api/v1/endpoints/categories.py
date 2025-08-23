from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.models.category import Category as CategoryModel
from src.schemas.category import Category, CategoryCreate, CategoryUpdate
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_categories_permissions

router = APIRouter()


@router.get("", response_model=list[Category])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    result = await db.execute(select(CategoryModel))
    return result.scalars().all()


@router.post("", response_model=Category)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.CREATE))
):
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    category = await db.get(CategoryModel, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    category = await db.get(CategoryModel, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category_update.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    category = await db.get(CategoryModel, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()
