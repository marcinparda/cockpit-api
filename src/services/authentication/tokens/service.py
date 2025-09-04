import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError, jwt
from src.core.config import settings
from src.services.authentication.tokens.repository import (
    create_access_token_record,
    create_refresh_token_record,
    get_access_token_by_jti,
    get_refresh_token_by_jti,
    update_access_token_revoked_status,
    update_refresh_token_revoked_status,
    update_access_token_last_used,
)


def create_access_token_jwt(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
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


def create_refresh_token_jwt(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
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


async def verify_token(token: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        # Basic format validation
        if not token or len(token.split('.')) != 3:
            raise JWTError("Invalid token format: not a valid JWT")
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM])

        user_id: Optional[str] = payload.get("sub")
        jti: Optional[str] = payload.get("jti")

        if user_id is None:
            raise JWTError("Token missing user identifier")

        # Check if token is revoked in database (if database session provided)
        if db and jti:

            token_type = payload.get("token_type", "access")
            is_valid = False

            if token_type == "refresh":
                is_valid = await is_refresh_token_valid(db, jti)
            else:
                is_valid = await is_access_token_valid(db, jti)
                # Update last used timestamp for access tokens
                await update_access_token_last_used_timestamp(db, jti)

            if not is_valid:
                raise JWTError("Token has been invalidated")

        return payload

    except JWTError:
        raise
    except ValueError as e:
        # Handle UUID conversion errors
        raise JWTError(f"Invalid token format: {e}")
    except Exception as e:
        # Handle any other JWT parsing errors
        raise JWTError(f"Token verification failed: {str(e)}")


async def invalidate_token(token: str, db: Optional[AsyncSession] = None) -> bool:
    """Invalidate a JWT token by revoking it in the database."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM])

        jti = payload.get("jti")

        if not jti:
            return False

        if db:
            token_type = payload.get("token_type", "access")
            if token_type == "refresh":
                return await update_refresh_token_revoked_status(db, jti, True)
            else:
                return await update_access_token_revoked_status(db, jti, True)

        return True  # Fallback to success if no database session
    except JWTError:
        return False


def extract_token_id(token: str) -> Optional[str]:
    """Extract the JWT ID from a token without full verification."""
    try:
        # Decode without verification to get JTI
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM],
                             options={"verify_signature": False})
        return payload.get("jti")
    except JWTError:
        return None


async def create_tokens_with_storage(
    user_id: UUID,
    email: str,
    db: AsyncSession
) -> Tuple[str, str]:
    """Create access and refresh tokens with database storage."""
    access_token_expires = timedelta(hours=settings.JWT_EXPIRE_HOURS)
    refresh_token_expires = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

    access_token_data = {"sub": str(user_id), "email": email}
    refresh_token_data = {"sub": str(user_id), "email": email}

    access_token = create_access_token_jwt(
        data=access_token_data,
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token_jwt(
        data=refresh_token_data,
        expires_delta=refresh_token_expires
    )

    # Extract JTIs and expiration times
    access_payload = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    refresh_payload = jwt.decode(
        refresh_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    access_jti = access_payload.get("jti")
    refresh_jti = refresh_payload.get("jti")
    access_exp_timestamp = access_payload.get("exp")
    refresh_exp_timestamp = refresh_payload.get("exp")

    if not access_exp_timestamp or not refresh_exp_timestamp:
        raise JWTError("Missing expiration in token payload")

    access_exp = datetime.fromtimestamp(
        access_exp_timestamp, tz=timezone.utc)
    refresh_exp = datetime.fromtimestamp(
        refresh_exp_timestamp, tz=timezone.utc)

    if access_jti:
        await create_access_token(db, access_jti, user_id, access_exp)
    if refresh_jti:
        await create_refresh_token(db, refresh_jti, user_id, refresh_exp)

    return access_token, refresh_token


async def create_access_token(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
):
    """Create a new access token record with timezone handling."""
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    return await create_access_token_record(db, jti, user_id, expires_at)


async def create_refresh_token(
    db: AsyncSession,
    jti: str,
    user_id: UUID,
    expires_at: datetime
):
    """Create a new refresh token record with timezone handling."""
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    return await create_refresh_token_record(db, jti, user_id, expires_at)


async def is_access_token_valid(db: AsyncSession, jti: str) -> bool:
    """Check if an access token is valid (exists, not revoked, not expired)."""
    token = await get_access_token_by_jti(db, jti)

    if not token:
        return False

    if token.is_revoked:
        return False

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if token.expires_at <= now:
        return False

    return True


async def is_refresh_token_valid(db: AsyncSession, jti: str) -> bool:
    """Check if a refresh token is valid (exists, not revoked, not expired)."""
    token = await get_refresh_token_by_jti(db, jti)

    if not token:
        return False

    if token.is_revoked:
        return False

    # Check if token is expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if token.expires_at <= now:
        return False

    return True


async def update_access_token_last_used_timestamp(db: AsyncSession, jti: str) -> bool:
    """Update the last_used_at timestamp for an access token."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return await update_access_token_last_used(db, jti, now)


async def refresh_access_token(refresh_token: str, db: AsyncSession):
    """
    Create new access token using refresh token.

    Args:
        refresh_token: Valid refresh token
        db: Database session for token operations

    Returns:
        Tuple of (new_access_token, new_refresh_token)

    Raises:
        JWTError: If refresh token is invalid or expired
    """
    from fastapi import HTTPException, status

    try:
        payload = await verify_token(refresh_token, db)

        # Verify it's a refresh token
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type - not a refresh token"
            )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload - missing required fields"
            )

        await invalidate_token(refresh_token, db)

        # Create new tokens
        return await create_tokens_with_storage(UUID(user_id), email, db)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid refresh token: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )
