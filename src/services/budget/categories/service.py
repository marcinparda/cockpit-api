"""Category service for category management operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.budget.categories.models import Category
from src.services.budget.categories import repository
from .schemas import CategoryCreate, CategoryUpdate


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
    """
    Get category by ID.

    Args:
        db: Database session
        category_id: Category ID

    Returns:
        Category object if found, None otherwise
    """
    return await repository.get_category_by_id(db, category_id)


async def get_all_categories(db: AsyncSession) -> Sequence[Category]:
    """
    Get all categories.

    Args:
        db: Database session

    Returns:
        Sequence of all categories
    """
    return await repository.get_all_categories(db)


async def create_category(
    db: AsyncSession,
    category_data: CategoryCreate
) -> Category:
    """
    Create a new category.

    Args:
        db: Database session
        category_data: Category creation data

    Returns:
        Created Category object
    """
    category = Category(**category_data.model_dump())
    return await repository.save_category(db, category)


async def update_category(
    db: AsyncSession,
    category_id: int,
    category_data: CategoryUpdate
) -> Optional[Category]:
    """
    Update an existing category.

    Args:
        db: Database session
        category_id: Category ID
        category_data: Updated category data

    Returns:
        Updated Category object, None if not found
    """
    category = await repository.get_category_by_id(db, category_id)
    if not category:
        return None

    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    return await repository.update_category(db, category)


async def delete_category(db: AsyncSession, category_id: int) -> bool:
    """
    Delete a category.

    Args:
        db: Database session
        category_id: Category ID

    Returns:
        True if category was deleted, False if not found
    """
    category = await repository.get_category_by_id(db, category_id)
    if not category:
        return False

    await repository.delete_category_record(db, category)
    return True
