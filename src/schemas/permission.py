from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from .feature import Feature
from .action import Action


class PermissionBase(BaseModel):
    """Base permission schema."""
    feature_id: UUID
    action_id: UUID


class PermissionCreate(PermissionBase):
    """Schema for creating a new permission."""
    pass


class PermissionUpdate(PermissionBase):
    """Schema for updating a permission."""
    pass


class PermissionInDBBase(PermissionBase):
    """Base schema for permission data from database."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Permission(PermissionInDBBase):
    """Permission schema for API responses."""
    pass


class PermissionWithDetails(Permission):
    """Permission schema with feature and action details."""
    feature: Feature
    action: Action
