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
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user_id: UUID
    email: str
    is_active: bool
    password_changed: bool


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        from src.auth.password import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError(
                f"Password validation failed: {', '.join(errors)}")
        return v


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: UUID  # subject (user_id)
    email: str
    exp: int   # expiration timestamp
    iat: int   # issued at timestamp
    jti: Optional[str] = None  # JWT ID for blacklist tracking


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh endpoint."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema for logout request."""
    refresh_token: Optional[str] = None
