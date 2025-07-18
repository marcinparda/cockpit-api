from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRoleBase(BaseModel):
    """Base schema for user role."""
    name: str
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UserRoleCreate(UserRoleBase):
    """Schema for creating a new user role."""
    pass


class UserRoleUpdate(UserRoleBase):
    """Schema for updating an existing user role."""
    pass


class UserRoleInDBBase(UserRoleBase):
    """Schema for user role in database."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRole(UserRoleInDBBase):
    """Schema for user role response."""
    pass
