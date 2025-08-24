from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
from src.app.auth.schemas import UserRole, Permission


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: Optional[str] = None
    role_id: UUID

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError(
                "Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role_id: Optional[UUID] = None


class UserInDBBase(UserBase):
    """Base schema for user data from database."""
    id: UUID
    role_id: UUID
    password_changed: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class User(UserInDBBase):
    """Public user schema without sensitive data."""
    pass


class SimpleUserResponse(BaseModel):
    """Schema for user ID and email."""
    id: UUID
    email: EmailStr

    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    """Internal user schema with password hash."""
    password_hash: str


class UserWithRole(User):
    """User schema with role information."""
    role: UserRole


class UserWithPermissions(User):
    """User schema with permissions information."""
    role: UserRole
    permissions: List[Permission]


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError(
                "Password must contain at least one special character")
        return v


class UserPermissionAssign(BaseModel):
    """Schema for assigning permissions to user."""
    permission_ids: List[UUID]


class UserPermissionRevoke(BaseModel):
    """Schema for revoking permission from user."""
    permission_id: UUID


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    new_password: Optional[str] = None


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    message: str
    new_password: str


class UserPermissionAssignResponse(BaseModel):
    """Response model for permission assignment endpoint."""
    message: str
    assigned_permissions: int
