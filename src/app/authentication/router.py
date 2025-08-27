"""Authentication endpoints for user login and password management."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.authentication.schemas import (
    LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse,
    SimpleRefreshResponse,
    UserInfoResponse,
)
from src.app.authentication.auth_service import (
    login_user
)
from src.app.users.service import change_user_password
from src.app.authentication.jwt_dependencies import get_current_active_user
from src.app.authentication.jwt_service import invalidate_token, refresh_access_token
from src.app.authentication.cookie_utils import set_auth_cookies, clear_auth_cookies
from src.app.authentication.exception_utils import (
    login_exception_handler,
    password_change_exception_handler,
    token_refresh_exception_handler,
    logout_exception_handler
)
from src.app.users.models import User
from src.core.config import settings


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
@login_exception_handler
async def login(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Authenticate user with email and password."""
    return await login_user(
        db=db,
        email=login_request.email,
        password=login_request.password,
        response=response
    )


@router.post("/change-password", response_model=PasswordChangeResponse)
@password_change_exception_handler
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PasswordChangeResponse:
    """Change current user's password."""
    success = await change_user_password(
        db=db,
        user_id=UUID(str(current_user.id)),
        current_password=password_request.current_password,
        new_password=password_request.new_password
    )

    if success:
        return PasswordChangeResponse(message="Password changed successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information."""
    return UserInfoResponse(
        user_id=UUID(str(current_user.id)),
        email=str(current_user.email),
        is_active=bool(current_user.is_active),
        password_changed=bool(current_user.password_changed),
        created_at=current_user.created_at.isoformat()
    )


@router.post("/refresh", response_model=SimpleRefreshResponse)
@token_refresh_exception_handler
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> SimpleRefreshResponse:
    """Refresh access token using refresh token from cookie."""

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required in cookie"
        )

    new_access_token, new_refresh_token = await refresh_access_token(refresh_token, db)

    set_auth_cookies(response, new_access_token, new_refresh_token)

    return SimpleRefreshResponse(message="Tokens refreshed successfully")


@router.post("/logout")
@logout_exception_handler
async def logout(
    request: Request,
    response: Response,
    # Cookie tokens
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db)
):
    """Logout the user by invalidating their tokens and clearing cookies."""
    # Get the access token from cookie or authorization header
    access_token = access_token_cookie
    refresh_token = refresh_token_cookie

    # If no cookie tokens, try Bearer token
    if not access_token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.replace("Bearer ", "")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token is required for logout"
        )

    # Invalidate the access token
    await invalidate_token(access_token, db)

    # Invalidate refresh token if available
    if refresh_token:
        await invalidate_token(refresh_token, db)

    # Clear httpOnly cookies
    clear_auth_cookies(response)

    return {"detail": "Successfully logged out"}
