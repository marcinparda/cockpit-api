from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from src.models.user import User
from src.auth.password import verify_password
from src.auth.jwt import (
    create_token_response, create_refresh_token_response,
    refresh_access_token, invalidate_token, verify_token
)
from src.schemas.auth import LoginResponse, TokenResponse, RefreshTokenResponse


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()

    if not user:
        return None

    # Check if user is active
    if user.is_active is False:
        return None

    # Verify password
    if not verify_password(password, str(user.password_hash)):
        return None

    return user


async def create_user_token(user: User) -> TokenResponse:
    """
    Create JWT token for authenticated user.

    Args:
        user: Authenticated user object

    Returns:
        TokenResponse with access token and metadata
    """
    from uuid import UUID

    user_id = UUID(str(user.id))
    email = str(user.email)

    return create_token_response(user_id, email)


async def login_user(db: AsyncSession, email: str, password: str) -> LoginResponse:
    """
    Complete login flow for user authentication with refresh token.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password

    Returns:
        LoginResponse with access token, refresh token and user details

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = await authenticate_user(db, email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create token pair (access + refresh)
    token_response = await create_user_refresh_token(user)

    # Create complete login response
    return LoginResponse(
        access_token=token_response.access_token,
        refresh_token=token_response.refresh_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
        refresh_expires_in=token_response.refresh_expires_in,
        user_id=UUID(str(user.id)),
        email=str(user.email),
        is_active=bool(user.is_active),
        password_changed=bool(user.password_changed)
    )


async def create_user_refresh_token(user: User) -> RefreshTokenResponse:
    """
    Create JWT token pair (access + refresh) for authenticated user.

    Args:
        user: Authenticated user object

    Returns:
        RefreshTokenResponse with access token, refresh token and metadata
    """
    from uuid import UUID

    user_id = UUID(str(user.id))
    email = str(user.email)

    return create_refresh_token_response(user_id, email)


async def refresh_user_tokens(refresh_token: str) -> RefreshTokenResponse:
    """
    Refresh user access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        RefreshTokenResponse with new access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        new_access_token, new_refresh_token = await refresh_access_token(
            refresh_token)

        # Extract user info from new access token for response
        payload = await verify_token(new_access_token)

        # Create response with new tokens
        from src.core.config import settings

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            refresh_expires_in=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


async def logout_user(access_token: str, refresh_token: Optional[str] = None) -> bool:
    """
    Logout user by invalidating tokens.

    Args:
        access_token: User's access token
        refresh_token: Optional refresh token to invalidate

    Returns:
        True if logout successful, False otherwise
    """
    try:
        # Invalidate access token
        access_invalidated = await invalidate_token(access_token)

        # Invalidate refresh token if provided
        refresh_invalidated = True
        if refresh_token:
            refresh_invalidated = await invalidate_token(refresh_token)

        return access_invalidated and refresh_invalidated

    except Exception:
        return False
