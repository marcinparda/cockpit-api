"""JWT token handling utilities for user authentication."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from jose import JWTError, jwt

from src.core.config import settings
from src.schemas.auth import TokenData, TokenResponse, RefreshTokenResponse
from src.auth.jwt_blacklist import is_token_blacklisted, blacklist_token


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

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32)  # JWT ID for blacklist tracking
    })

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),  # JWT ID for blacklist tracking
        "token_type": "refresh"
    })

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
        jti: Optional[str] = payload.get("jti")

        if user_id is None:
            raise JWTError("Token missing user identifier")

        # Check if token is blacklisted
        if jti and is_token_blacklisted(jti):
            raise JWTError("Token has been invalidated")

        return payload

    except JWTError:
        raise
    except ValueError as e:
        # Handle UUID conversion errors
        raise JWTError(f"Invalid token format: {e}")


def invalidate_token(token: str) -> bool:
    """
    Invalidate a JWT token by adding it to the blacklist.

    Args:
        token: The JWT token to invalidate

    Returns:
        True if token was successfully invalidated, False otherwise
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM])

        jti = payload.get("jti")
        exp = payload.get("exp")

        if jti and exp:
            blacklist_token(jti, exp)
            return True

        return False
    except JWTError:
        return False


def extract_token_id(token: str) -> Optional[str]:
    """
    Extract the JWT ID from a token without full verification.

    Args:
        token: The JWT token

    Returns:
        JWT ID if present, None otherwise
    """
    try:
        # Decode without verification to get JTI
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM],
                             options={"verify_signature": False})
        return payload.get("jti")
    except JWTError:
        return None


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


def create_refresh_token_response(user_id: UUID, email: str) -> RefreshTokenResponse:
    """
    Create a complete refresh token response for login.

    Args:
        user_id: The user's UUID
        email: The user's email address

    Returns:
        RefreshTokenResponse containing access token, refresh token and metadata
    """
    access_token_expires = timedelta(hours=settings.JWT_EXPIRE_HOURS)
    refresh_token_expires = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": str(user_id), "email": email},
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user_id), "email": email},
        expires_delta=refresh_token_expires
    )

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_HOURS * 3600,  # Convert hours to seconds
        refresh_expires_in=settings.JWT_REFRESH_EXPIRE_DAYS *
        24 * 3600  # Convert days to seconds
    )


def refresh_access_token(refresh_token: str) -> Tuple[str, str]:
    """
    Create new access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        Tuple of (new_access_token, new_refresh_token)

    Raises:
        JWTError: If refresh token is invalid or expired
    """
    try:
        payload = verify_token(refresh_token)

        # Verify it's a refresh token
        if payload.get("token_type") != "refresh":
            raise JWTError("Invalid token type")

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise JWTError("Invalid token payload")

        # Invalidate old refresh token
        invalidate_token(refresh_token)

        # Create new tokens
        response = create_refresh_token_response(UUID(user_id), email)
        return response.access_token, response.refresh_token

    except JWTError:
        raise
    except ValueError as e:
        raise JWTError(f"Invalid user ID format: {e}")
