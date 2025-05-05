from pydantic import BaseModel

from datetime import datetime


class PermissionBase(BaseModel):
    feature: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(PermissionBase):
    pass


class PermissionInDBBase(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Permission(PermissionInDBBase):
    pass
