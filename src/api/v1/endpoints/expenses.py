from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.models.expense import Expense as ExpenseModel
from src.schemas.expense import Expense, ExpenseCreate, ExpenseUpdate

router = APIRouter()


@router.get("/", response_model=list[Expense])
async def list_expenses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExpenseModel))
    return result.scalars().all()


@router.post("/", response_model=Expense)
async def create_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    db_expense = ExpenseModel(**expense.dict())
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


@router.get("/{expense_id}", response_model=Expense)
async def get_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    expense = await db.get(ExpenseModel, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(expense_id: int, expense_update: ExpenseUpdate, db: AsyncSession = Depends(get_db)):
    expense = await db.get(ExpenseModel, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in expense_update.dict(exclude_unset=True).items():
        setattr(expense, key, value)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    expense = await db.get(ExpenseModel, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
