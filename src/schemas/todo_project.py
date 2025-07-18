from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TodoProjectBase(BaseModel):
    name: str


class TodoProjectCreate(TodoProjectBase):
    pass


class TodoProjectUpdate(TodoProjectBase):
    pass


class TodoProjectInDBBase(TodoProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodoProject(TodoProjectInDBBase):
    pass
