"""Expense service for expense management operations."""

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.services.budget.expenses.models import Expense
from src.services.budget.expenses import repository
from src.services.budget.categories.service import get_category_by_id
from src.services.budget.payment_methods.service import get_payment_method_by_id
from .schemas import ExpenseCreate, ExpenseUpdate


async def get_expense_by_id(db: AsyncSession, expense_id: int) -> Optional[Expense]:
    """
    Get expense by ID.

    Args:
        db: Database session
        expense_id: Expense ID

    Returns:
        Expense object if found, None otherwise
    """
    return await repository.get_expense_by_id(db, expense_id)


async def get_all_expenses(db: AsyncSession) -> Sequence[Expense]:
    """
    Get all expenses.

    Args:
        db: Database session

    Returns:
        Sequence of all expenses
    """
    return await repository.get_all_expenses(db)


async def create_expense(
    db: AsyncSession,
    expense_data: ExpenseCreate
) -> Expense:
    """
    Create a new expense.

    Args:
        db: Database session
        expense_data: Expense creation data

    Returns:
        Created Expense object

    Raises:
        HTTPException: If category_id or payment_method_id doesn't exist
    """
    category = await get_category_by_id(db, expense_data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with ID {expense_data.category_id} does not exist"
        )

    payment_method = await get_payment_method_by_id(db, expense_data.payment_method_id)
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method with ID {expense_data.payment_method_id} does not exist"
        )

    expense = Expense(**expense_data.model_dump())
    return await repository.save_expense(db, expense)


async def update_expense(
    db: AsyncSession,
    expense_id: int,
    expense_data: ExpenseUpdate
) -> Optional[Expense]:
    """
    Update an existing expense.

    Args:
        db: Database session
        expense_id: Expense ID
        expense_data: Updated expense data

    Returns:
        Updated Expense object, None if not found

    Raises:
        HTTPException: If category_id or payment_method_id doesn't exist
    """
    expense = await repository.get_expense_by_id(db, expense_id)
    if not expense:
        return None

    update_data = expense_data.model_dump(exclude_unset=True)
    
    if "category_id" in update_data:
        category = await get_category_by_id(db, update_data["category_id"])
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {update_data['category_id']} does not exist"
            )

    if "payment_method_id" in update_data:
        payment_method = await get_payment_method_by_id(db, update_data["payment_method_id"])
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment method with ID {update_data['payment_method_id']} does not exist"
            )

    for key, value in update_data.items():
        setattr(expense, key, value)

    return await repository.update_expense(db, expense)


async def delete_expense(db: AsyncSession, expense_id: int) -> bool:
    """
    Delete an expense.

    Args:
        db: Database session
        expense_id: Expense ID

    Returns:
        True if expense was deleted, False if not found
    """
    expense = await repository.get_expense_by_id(db, expense_id)
    if not expense:
        return False

    await repository.delete_expense_record(db, expense)
    return True
