"""Permission system Pydantic schemas."""

from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class FeatureBase(BaseModel):
    """Base schema for features."""
    name: str


class Feature(FeatureBase):
    """Complete feature schema."""
    id: UUID

    class Config:
        from_attributes = True


class ActionBase(BaseModel):
    """Base schema for actions."""
    name: str


class Action(ActionBase):
    """Complete action schema."""
    id: UUID

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """Base schema for permissions."""
    feature_id: UUID
    action_id: UUID


class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""
    pass


class Permission(PermissionBase):
    """Complete permission schema."""
    id: UUID
    feature: Optional[Feature] = None
    action: Optional[Action] = None

    class Config:
        from_attributes = True
