from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)


class APIKeyPermission(APIKeyPermissionInDBBase):
    pass
