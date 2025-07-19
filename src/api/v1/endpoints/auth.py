"""Authentication endpoints for user login and password management."""

from uuid import UUID
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.auth import (
    LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    UserInfoResponse
)
from src.services.auth_service import (
    login_user, refresh_user_tokens
)
from src.services.user_service import change_user_password
from src.auth.jwt_dependencies import get_current_active_user, get_current_user
from src.auth.dependencies import require_admin_role
from src.auth.jwt import invalidate_token
from src.models.user import User
from src.services.task_service import TokenCleanupService
from src.core.config import settings

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
        refresh_response = await refresh_user_tokens(refresh_request.refresh_token, db)
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


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Logout the user by invalidating their tokens."""
    try:
        # Get the access token from the authorization header
        access_token = request.headers.get(
            "authorization", "").replace("Bearer ", "")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access token is required for logout"
            )

        # Invalidate the access token
        await invalidate_token(access_token, db)

        return {"detail": "Successfully logged out"}

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


@router.get("/tokens/statistics", response_model=Dict[str, Any], tags=["admin"])
async def token_statistics(
    admin_user: User = Depends(require_admin_role)
):
    """
    Get current token statistics for monitoring (admin only).

    Returns detailed statistics about:
    - Active tokens
    - Expired tokens  
    - Revoked tokens
    - Total counts
    """
    try:
        stats_result = await TokenCleanupService.get_cleanup_statistics()

        if not stats_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get token statistics: {stats_result.get('error', 'Unknown error')}"
            )

        return stats_result["statistics"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get token statistics: {str(e)}"
        )


@router.post("/cleanup/manual", response_model=Dict[str, Any], tags=["admin"])
async def trigger_manual_cleanup(
    admin_user: User = Depends(require_admin_role)
):
    """
    Trigger a manual token cleanup operation (admin only).

    This endpoint allows administrators to manually trigger
    the cleanup process outside of the scheduled runs.

    Note: This should be used sparingly and primarily for
    maintenance or emergency cleanup scenarios.
    """
    try:
        from src.tasks.token_cleanup import manual_token_cleanup

        cleanup_result = await manual_token_cleanup(
            cleanup_expired=True,
            cleanup_revoked=True,
            retention_days=settings.TOKEN_CLEANUP_RETENTION_DAYS,
            dry_run=False
        )

        if not cleanup_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Manual cleanup failed: {cleanup_result.get('error', 'Unknown error')}"
            )

        return cleanup_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute manual cleanup: {str(e)}"
        )


@router.post("/cleanup/dry-run", response_model=Dict[str, Any], tags=["admin"])
async def dry_run_cleanup(
    admin_user: User = Depends(require_admin_role)
):
    """
    Perform a dry run of the token cleanup process (admin only).

    This endpoint simulates the cleanup process without
    actually deleting any tokens, providing information
    about what would be cleaned up.
    """
    try:
        from src.tasks.token_cleanup import manual_token_cleanup

        dry_run_result = await manual_token_cleanup(
            cleanup_expired=True,
            cleanup_revoked=True,
            retention_days=settings.TOKEN_CLEANUP_RETENTION_DAYS,
            dry_run=True
        )

        return dry_run_result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute cleanup dry run: {str(e)}"
        )
