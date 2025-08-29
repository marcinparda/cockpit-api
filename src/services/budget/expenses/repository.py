"""Expense repository for database operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.services.budget.expenses.models import Expense


async def get_expense_by_id(db: AsyncSession, expense_id: int) -> Optional[Expense]:
    """Get expense by ID."""
    return await db.get(Expense, expense_id)


async def get_all_expenses(db: AsyncSession) -> Sequence[Expense]:
    """Get all expenses."""
    result = await db.execute(select(Expense))
    return result.scalars().all()


async def save_expense(db: AsyncSession, expense: Expense) -> Expense:
    """Save expense to database."""
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def update_expense(db: AsyncSession, expense: Expense) -> Expense:
    """Update expense in database."""
    await db.commit()
    await db.refresh(expense)
    return expense


async def delete_expense_record(db: AsyncSession, expense: Expense) -> None:
    """Delete expense record from database."""
    await db.delete(expense)
    await db.commit()