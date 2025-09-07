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


def _validate_token_format(token: str) -> None:
    """Validate basic JWT token format."""
    if not token or len(token.split('.')) != 3:
        raise JWTError("Invalid token format: not a valid JWT")


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    """Decode JWT and extract payload."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def _validate_payload_claims(payload: Dict[str, Any]) -> None:
    """Validate required JWT payload claims."""
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise JWTError("Token missing user identifier")


async def _verify_token_in_database(
    db: AsyncSession,
    payload: Dict[str, Any],
    jti: str
) -> None:
    """Verify token validity in database."""
    token_type = payload.get("token_type", "access")
    is_valid = False

    if token_type == "refresh":
        is_valid = await is_refresh_token_valid(db, jti)
    else:
        is_valid = await is_access_token_valid(db, jti)
        await update_access_token_last_used_timestamp(db, jti)

    if not is_valid:
        raise JWTError("Token has been invalidated")


async def verify_token(token: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        _validate_token_format(token)
        payload = _decode_jwt_payload(token)
        _validate_payload_claims(payload)

        if db:
            jti = payload.get("jti")
            if jti:
                await _verify_token_in_database(db, payload, jti)

        return payload

    except JWTError:
        raise
    except ValueError as e:
        raise JWTError(f"Invalid token format: {e}")
    except Exception as e:
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


def _create_token_data(user_id: UUID, email: str) -> Dict[str, str]:
    """Create token payload data."""
    return {"sub": str(user_id), "email": email}


def _get_token_expiration_deltas() -> Tuple[timedelta, timedelta]:
    """Get access and refresh token expiration deltas."""
    return (
        timedelta(hours=settings.JWT_EXPIRE_HOURS),
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )


def _extract_token_metadata(token: str) -> Tuple[str, int]:
    """Extract JTI and expiration timestamp from token."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    jti = payload.get("jti")
    exp_timestamp = payload.get("exp")
    
    if not jti or not exp_timestamp:
        raise JWTError("Missing required token metadata (jti or exp)")
        
    return jti, exp_timestamp


async def _store_tokens_in_database(
    db: AsyncSession,
    access_token: str,
    refresh_token: str,
    user_id: UUID
) -> None:
    """Store token metadata in database."""
    access_jti, access_exp_timestamp = _extract_token_metadata(access_token)
    refresh_jti, refresh_exp_timestamp = _extract_token_metadata(refresh_token)

    access_exp = datetime.fromtimestamp(access_exp_timestamp, tz=timezone.utc)
    refresh_exp = datetime.fromtimestamp(refresh_exp_timestamp, tz=timezone.utc)

    await create_access_token(db, access_jti, user_id, access_exp)
    await create_refresh_token(db, refresh_jti, user_id, refresh_exp)


async def create_tokens_with_storage(
    user_id: UUID,
    email: str,
    db: AsyncSession
) -> Tuple[str, str]:
    """Create access and refresh tokens with database storage."""
    access_token_expires, refresh_token_expires = _get_token_expiration_deltas()
    token_data = _create_token_data(user_id, email)

    access_token = create_access_token_jwt(
        data=token_data,
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token_jwt(
        data=token_data,
        expires_delta=refresh_token_expires
    )

    await _store_tokens_in_database(db, access_token, refresh_token, user_id)

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


def _validate_refresh_token_type(payload: Dict[str, Any]) -> None:
    """Validate that token is a refresh token."""
    from fastapi import HTTPException, status
    
    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type - not a refresh token"
        )


def _extract_user_credentials(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Extract user ID and email from token payload."""
    from fastapi import HTTPException, status
    
    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload - missing required fields"
        )

    return user_id, email


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
        _validate_refresh_token_type(payload)
        user_id, email = _extract_user_credentials(payload)

        await invalidate_token(refresh_token, db)
        return await create_tokens_with_storage(UUID(user_id), email, db)

    except HTTPException:
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
