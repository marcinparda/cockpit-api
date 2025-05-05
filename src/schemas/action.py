from pydantic import BaseModel

from datetime import datetime


class ActionBase(BaseModel):
    name: str


class ActionCreate(ActionBase):
    pass


class ActionUpdate(ActionBase):
    pass


class ActionInDBBase(ActionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Action(ActionInDBBase):
    pass
