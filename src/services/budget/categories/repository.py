"""Category repository for database operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.services.budget.categories.models import Category


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
    """Get category by ID."""
    return await db.get(Category, category_id)


async def get_all_categories(db: AsyncSession) -> Sequence[Category]:
    """Get all categories."""
    result = await db.execute(select(Category))
    return result.scalars().all()


async def save_category(db: AsyncSession, category: Category) -> Category:
    """Save category to database."""
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_category(db: AsyncSession, category: Category) -> Category:
    """Update category in database."""
    await db.commit()
    await db.refresh(category)
    return category


async def delete_category_record(db: AsyncSession, category: Category) -> None:
    """Delete category record from database."""
    await db.delete(category)
    await db.commit()
