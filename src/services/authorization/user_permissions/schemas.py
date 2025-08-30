"""User permission Pydantic schemas."""

from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from src.services.authorization.permissions.schemas import Permission


class UserPermissionBase(BaseModel):
    """Base schema for user permissions."""
    user_id: UUID
    permission_id: UUID


class UserPermissionCreate(UserPermissionBase):
    """Schema for creating a user permission."""
    pass


class UserPermissionUpdate(BaseModel):
    """Schema for updating a user permission."""
    permission_id: Optional[UUID] = None


class UserPermission(UserPermissionBase):
    """Complete user permission schema."""
    id: UUID
    permission: Optional[Permission] = None

    class Config:
        from_attributes = True
