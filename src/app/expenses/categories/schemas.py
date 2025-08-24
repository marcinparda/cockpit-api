from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryInDBBase(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDBBase):
    pass


class CategoryWithChildren(CategoryInDBBase):
    children: List["CategoryWithChildren"] = []
