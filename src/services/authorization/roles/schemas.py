"""Role-related Pydantic schemas."""

from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class UserRoleBase(BaseModel):
    """Base schema for user roles."""
    name: str
    description: Optional[str] = None


class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role."""
    pass


class UserRoleUpdate(BaseModel):
    """Schema for updating a user role."""
    name: Optional[str] = None
    description: Optional[str] = None


class UserRole(UserRoleBase):
    """Complete user role schema."""
    id: UUID

    class Config:
        from_attributes = True