"""Session management schemas."""

from uuid import UUID
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response model for login endpoint."""
    detail: str


class LogoutResponse(BaseModel):
    """Response model for logout endpoint."""
    detail: str


class UserInfoResponse(BaseModel):
    """Response model for user information endpoint."""
    user_id: UUID
    email: str
    is_active: bool
    password_changed: bool
    created_at: str  # ISO format datetime string