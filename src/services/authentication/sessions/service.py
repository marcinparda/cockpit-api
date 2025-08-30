"""Session management service."""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response, HTTPException, status

from src.services.users.models import User
from src.services.users.service import get_user_by_email
from src.services.authentication.sessions.schemas import LoginResponse
from src.services.authentication.tokens.service import create_tokens_with_storage, invalidate_token
from src.services.authentication.sessions.cookie_utils import set_auth_cookies, clear_auth_cookies
from src.services.authentication.passwords.service import verify_password


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
    user = await authenticate_user(db, email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await create_tokens_with_storage(
        user_id=UUID(str(user.id)),
        email=str(user.email),
        db=db
    )

    if response:
        set_auth_cookies(response, access_token, refresh_token)

    return LoginResponse(message="Login successful")


async def logout(response, access_token_cookie: Optional[str], refresh_token_cookie: Optional[str], db: AsyncSession) -> dict:
    """Logout the user by invalidating their tokens and clearing cookies."""
    if access_token_cookie:
        await invalidate_token(access_token_cookie, db)

    if refresh_token_cookie:
        await invalidate_token(refresh_token_cookie, db)

    clear_auth_cookies(response)

    return {"message": "Logout successful"}


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
    user = await get_user_by_email(db, email)

    if not user:
        return None

    if bool(user.is_active) is False:
        return None

    if not verify_password(password, str(user.password_hash)):
        return None

    return user
