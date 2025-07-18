"""Authentication schemas for JWT tokens and user authentication."""

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
