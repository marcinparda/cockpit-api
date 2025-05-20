from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ShoppingItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    categories: Optional[str] = None
    shops: Optional[str] = None


class ShoppingItemCreate(ShoppingItemBase):
    pass


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_closed: Optional[bool] = None
    categories: Optional[str] = None
    shops: Optional[str] = None
    completed_at: Optional[datetime] = None


class ShoppingItemInDBBase(ShoppingItemBase):
    id: int
    is_closed: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShoppingItem(ShoppingItemInDBBase):
    pass
