from pydantic import BaseModel

from datetime import datetime


class APIKeyPermissionBase(BaseModel):
    api_key_id: int
    permission_id: int


class APIKeyPermissionCreate(APIKeyPermissionBase):
    pass


class APIKeyPermissionUpdate(APIKeyPermissionBase):
    pass


class APIKeyPermissionInDBBase(APIKeyPermissionBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyPermission(APIKeyPermissionInDBBase):
    pass
