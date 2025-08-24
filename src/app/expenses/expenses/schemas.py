from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime


class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0)
    category_id: int
    payment_method_id: int
    date: date
    description: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseInDBBase(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Expense(ExpenseInDBBase):
    pass
