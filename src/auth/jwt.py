"""JWT token handling utilities for user authentication."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt

from src.core.config import settings
from src.schemas.auth import TokenData, TokenResponse


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(hours=settings.JWT_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        Dictionary containing the decoded payload

    Raises:
        JWTError: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM])

        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            raise JWTError("Token missing user identifier")

        return payload

    except JWTError:
        raise
    except ValueError as e:
        # Handle UUID conversion errors
        raise JWTError(f"Invalid token format: {e}")


def create_token_response(user_id: UUID, email: str) -> TokenResponse:
    """
    Create a complete token response for login.

    Args:
        user_id: The user's UUID
        email: The user's email address

    Returns:
        TokenResponse containing access token and metadata
    """
    access_token_expires = timedelta(hours=settings.JWT_EXPIRE_HOURS)

    access_token = create_access_token(
        data={"sub": str(user_id), "email": email},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )
