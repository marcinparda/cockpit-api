"""Session management endpoints for user login, logout, and user info."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.authentication.sessions.schemas import (
    LoginRequest, LoginResponse, UserInfoResponse
)
from src.services.authentication.sessions.service import login_user, secure_logout
from src.services.authentication.shared.dependencies import get_current_user
from src.services.authentication.shared.exception_utils import (
    login_exception_handler,
    logout_exception_handler
)
from src.services.users.models import User


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


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return UserInfoResponse(
        user_id=UUID(str(current_user.id)),
        email=str(current_user.email),
        is_active=bool(current_user.is_active),
        password_changed=bool(current_user.password_changed),
        created_at=current_user.created_at.isoformat()
    )


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

    return await secure_logout(
        # request=request,
        # response=response,
        # access_token_cookie=access_token_cookie,
        # refresh_token_cookie=refresh_token_cookie,
        # db=db
    )
