"""Authentication domain service for cross-subdomain business logic."""

from typing import Optional, Dict
from uuid import UUID
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.authentication.sessions.schemas import LoginResponse
from src.services.authentication.tokens.jwt_service import (
    create_tokens_with_storage, invalidate_token
)
from src.services.authentication.shared.cookie_utils import set_auth_cookies, clear_auth_cookies
from src.services.authentication.sessions.repository import get_user_by_email
from src.services.authentication.passwords.service import verify_password


class AuthService:
    """Domain service for authentication business logic coordination."""

    async def _authenticate_user(self, db: AsyncSession, email: str, password: str):
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

    async def authenticate_and_create_session(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        response: Optional[Response] = None
    ) -> LoginResponse:
        """
        Complete login flow coordinating session creation and token generation.

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
        # Authenticate user
        user = await self._authenticate_user(db, email, password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens with storage
        access_token, refresh_token = await create_tokens_with_storage(
            user_id=UUID(str(user.id)),
            email=str(user.email),
            db=db
        )

        # Set authentication cookies if response provided
        if response:
            set_auth_cookies(response, access_token, refresh_token)

        return LoginResponse(message="Login successful")
