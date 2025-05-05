from pydantic import BaseModel
from typing import Optional, List, UUID, Dict
from datetime import datetime


class APIKeyBase(BaseModel):
    key: str
    is_active: bool = True
    created_by: Optional[UUID] = None


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
