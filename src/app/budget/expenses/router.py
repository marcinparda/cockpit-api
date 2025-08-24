from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from .schemas import Expense, ExpenseCreate, ExpenseUpdate
from .service import (
    get_all_expenses,
    get_expense_by_id,
    create_expense,
    update_expense,
    delete_expense
)
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_expenses_permissions

router = APIRouter()


@router.get("", response_model=list[Expense])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_expenses_permissions(Actions.READ))
):
    return await get_all_expenses(db)


@router.post("", response_model=Expense)
async def create_expense_endpoint(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_expenses_permissions(Actions.CREATE))
):
    return await create_expense(db, expense_data)


@router.get("/{expense_id}", response_model=Expense)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_expenses_permissions(Actions.READ))
):
    expense = await get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=Expense)
async def update_expense_endpoint(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_expenses_permissions(Actions.UPDATE))
):
    expense = await update_expense(db, expense_id, expense_data)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.delete("/{expense_id}", status_code=204)
async def delete_expense_endpoint(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(get_expenses_permissions(Actions.DELETE))
):
    deleted = await delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
