from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict
from datetime import datetime


class APIKeyBase(BaseModel):
    key: str
    is_active: bool = True
    created_by: Optional[UUID4] = None


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(APIKeyBase):
    key: Optional[str] = None
    is_active: Optional[bool] = None


class APIKeyInDBBase(APIKeyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKey(APIKeyInDBBase):
    pass


class APIKeyWithPermissions(APIKeyInDBBase):
    permissions: Dict[str, List[str]] = {}
