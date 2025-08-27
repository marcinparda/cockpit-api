from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Response

from src.app.users.models import User
from src.app.authentication.password_service import verify_password
from src.app.authentication.auth_repository import get_user_by_email
from src.app.authentication.jwt_service import (
    invalidate_token,
    create_tokens_with_storage
)
from src.app.authentication.schemas import LoginResponse


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
    user = await get_user_by_email(db, email)

    if not user:
        return None

    if bool(user.is_active) is False:
        return None

    # Verify password
    if not verify_password(password, str(user.password_hash)):
        return None

    return user


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
    access_token, refresh_token = await create_tokens_with_storage(user_id, email, db)

    # Set httpOnly cookies if response object is provided
    if response:
        from src.app.authentication.cookie_utils import set_auth_cookies
        set_auth_cookies(response, access_token, refresh_token)

    return LoginResponse(message="Successfully logged in")


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
