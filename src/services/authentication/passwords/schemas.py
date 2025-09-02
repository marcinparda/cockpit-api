"""Password management schemas."""

from pydantic import BaseModel, field_validator


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        from src.services.authentication.passwords.service import validate_password_strength

        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError(
                f"Password validation failed: {', '.join(errors)}")
        return v


class PasswordChangeResponse(BaseModel):
    """Response model for password change endpoint."""
    detail: str
