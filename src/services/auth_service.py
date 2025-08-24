from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status, Response
from typing import cast, Literal
from src.core.config import settings


from src.app.auth.models import User
from src.app.auth.password import verify_password
from src.app.auth.jwt import (
    create_token_response,
    refresh_access_token, invalidate_token, verify_token,
    create_refresh_token_response
)
from src.app.auth.schemas import LoginResponse, TokenResponse, RefreshTokenResponse


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


async def login_user(db: AsyncSession, email: str, password: str, response: Optional[Response] = None) -> LoginResponse:
    """
    Complete login flow for user authentication with refresh token.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        response: FastAPI Response object for setting cookies (optional)

    Returns:
        LoginResponse with success message

    Raises:
        HTTPException: If authentication fails
    """
    user = await authenticate_user(db, email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user_id = UUID(str(user.id))
    email = str(user.email)
    token_response = await create_refresh_token_response(user_id, email, db)

    # Set httpOnly cookies if response object is provided
    if response:
        # Environment-specific cookie settings
        is_production = settings.ENVIRONMENT == "production"
        cookie_domain = settings.COOKIE_DOMAIN if is_production else None
        cookie_secure = settings.COOKIE_SECURE if is_production else False
        cookie_samesite = settings.COOKIE_SAMESITE

        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            max_age=settings.ACCESS_TOKEN_COOKIE_MAX_AGE,
            httponly=settings.COOKIE_HTTPONLY,
            secure=cookie_secure,
            samesite=cookie_samesite,
            domain=cookie_domain
        )

        response.set_cookie(
            key="refresh_token",
            value=token_response.refresh_token,
            max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
            httponly=settings.COOKIE_HTTPONLY,
            secure=cookie_secure,
            samesite=cookie_samesite,
            domain=cookie_domain
        )

    return LoginResponse(message="Successfully logged in")


async def refresh_user_tokens(refresh_token: str, db: Optional[AsyncSession] = None) -> RefreshTokenResponse:
    """
    Refresh user access token using refresh token.

    Args:
        refresh_token: Valid refresh token
        db: Optional database session for token operations

    Returns:
        RefreshTokenResponse with new access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        new_access_token, new_refresh_token = await refresh_access_token(
            refresh_token, db)

        # Extract user info from new access token for response
        payload = await verify_token(new_access_token, db)

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


async def logout_user(access_token: str, refresh_token: Optional[str] = None, db: Optional[AsyncSession] = None) -> bool:
    """
    Logout user by invalidating tokens.

    Args:
        access_token: User's access token
        refresh_token: Optional refresh token to invalidate
        db: Optional database session for token operations

    Returns:
        True if logout successful, False otherwise
    """
    try:
        # Invalidate access token
        access_invalidated = await invalidate_token(access_token, db)

        # Invalidate refresh token if provided
        refresh_invalidated = True
        if refresh_token:
            refresh_invalidated = await invalidate_token(refresh_token, db)

        return access_invalidated and refresh_invalidated

    except Exception:
        return False
