"""Session management service."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response

from src.services.users.models import User
from src.services.authentication.sessions.repository import get_user_by_email
from src.services.authentication.passwords.service import verify_password
from src.services.authentication.sessions.schemas import LoginResponse
from src.services.authentication.shared.service import AuthService


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
    Complete login flow for user authentication with tokens.

    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        response: FastAPI response object for setting cookies

    Returns:
        LoginResponse with success message

    Raises:
        HTTPException: If authentication fails
    """

    domain_service = AuthService()
    return await domain_service.authenticate_and_create_session(
        db=db,
        email=email,
        password=password,
        response=response
    )


async def secure_logout() -> None:
    """
    Securely logout the user by invalidating their tokens and clearing cookies.

    Args:
        db: Database session
        access_token: Access token from cookie
        refresh_token: Refresh token from cookie
        response: FastAPI response object for clearing cookies

    Raises:
        HTTPException: If logout fails
    """

    pass
