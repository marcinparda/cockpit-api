"""Token management schemas."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class TokenData(BaseModel):
    """Token data model for JWT payload."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None


class TokenResponse(BaseModel):
    """Response model for token endpoint."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


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


class SimpleRefreshResponse(BaseModel):
    """Simple response model for refresh endpoint."""
    detail: str