"""Authentication endpoints for user login and password management."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.auth import (
    LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse,
    RefreshTokenRequest, RefreshTokenResponse, LogoutRequest, LogoutResponse,
    UserInfoResponse
)
from src.services.auth_service import (
    login_user, refresh_user_tokens, logout_user
)
from src.services.user_service import change_user_password
from src.auth.jwt_dependencies import get_current_active_user
from src.auth.jwt_dependencies import get_current_user_with_token
from src.models.user import User

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Authenticate user with email and password."""
    try:
        login_response = await login_user(
            db=db,
            email=login_request.email,
            password=login_request.password
        )
        return login_response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic message
        # TODO: Add proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> PasswordChangeResponse:
    """Change current user's password."""
    try:
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

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic message
        # TODO: Add proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change service temporarily unavailable"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "password_changed": current_user.password_changed,
        "created_at": current_user.created_at.isoformat()
    }


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_tokens(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> RefreshTokenResponse:
    """Refresh access token using refresh token."""
    try:
        refresh_response = await refresh_user_tokens(refresh_request.refresh_token)
        return refresh_response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic message
        # TODO: Add proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service temporarily unavailable"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    logout_request: LogoutRequest = LogoutRequest(),
    user_token: tuple[User, str] = Depends(get_current_user_with_token)
):
    """Logout user by invalidating tokens."""
    try:
        current_user, access_token = user_token

        # Logout user with both tokens
        success = await logout_user(access_token, logout_request.refresh_token)

        if success:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic message
        # TODO: Add proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service temporarily unavailable"
        )
