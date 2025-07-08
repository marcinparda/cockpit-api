from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from src.schemas.todo_project import TodoProject


class TodoItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    shops: Optional[str] = None
    project_id: Optional[int] = None


class TodoItemCreate(TodoItemBase):
    pass


class TodoItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_closed: Optional[bool] = None
    shops: Optional[str] = None
    completed_at: Optional[datetime] = None
    project_id: Optional[int] = None


class TodoItemInDBBase(TodoItemBase):
    id: int
    is_closed: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    project: Optional[TodoProject] = None

    class Config:
        from_attributes = True


class TodoItem(TodoItemInDBBase):
    pass
