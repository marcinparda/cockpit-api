"""Authentication and authorization schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# Authentication schemas
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
    """Response model for login endpoint."""
    message: str


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        from src.app.auth.password import validate_password_strength

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


class PasswordChangeResponse(BaseModel):
    """Response model for password change endpoint."""
    message: str


class UserInfoResponse(BaseModel):
    """Response model for user information endpoint."""
    user_id: UUID
    email: str
    is_active: bool
    password_changed: bool
    created_at: str  # ISO format datetime string


class LogoutResponse(BaseModel):
    """Response model for logout endpoint."""
    message: str


class SimpleRefreshResponse(BaseModel):
    """Simple response model for refresh endpoint."""
    message: str


# Action schemas
class ActionBase(BaseModel):
    name: str


class ActionCreate(ActionBase):
    pass


class ActionUpdate(ActionBase):
    pass


class ActionInDBBase(ActionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Action(ActionInDBBase):
    pass


# Feature schemas
class FeatureBase(BaseModel):
    name: str


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(FeatureBase):
    pass


class FeatureInDBBase(FeatureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Feature(FeatureInDBBase):
    pass


# Permission schemas
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


# User Role schemas
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