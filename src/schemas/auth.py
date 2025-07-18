"""Authentication schemas for JWT tokens and user authentication."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class TokenData(BaseModel):
    """Token data model for JWT payload."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None


class TokenResponse(BaseModel):
    """Response model for token endpoint."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    email: str
    role_name: str
    password_changed: bool


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: UUID  # subject (user_id)
    email: str
    exp: int   # expiration timestamp
    iat: int   # issued at timestamp
