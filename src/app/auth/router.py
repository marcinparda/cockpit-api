"""Authentication endpoints for user login and password management."""

from uuid import UUID
from typing import Dict, Any, cast, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.auth.schemas import (
    LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse,
    SimpleRefreshResponse,
    UserInfoResponse,
    Permission as PermissionSchema,
    UserRole as UserRoleSchema,
)
from src.services.auth_service import (
    login_user, refresh_user_tokens
)
from src.app.users.service import change_user_password, get_user_with_permissions, get_user_with_role, get_all_roles
from typing import List
from src.app.auth.jwt_dependencies import get_current_active_user
from src.app.auth.dependencies import require_admin_role
from src.app.auth.jwt import invalidate_token
from src.app.auth.models import User
from src.services.task_service import TokenCleanupService
from src.core.config import settings


router = APIRouter()


@router.get("/me/permissions", response_model=List[PermissionSchema])
async def get_current_user_permission(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permissions."""
    user = await get_user_with_permissions(db, UUID(str(current_user.id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [up.permission for up in user.permissions if up.permission]


@router.get("/me/roles", response_model=List[str])
async def get_current_user_roles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's roles as a list of role names (strings)."""
    user = await get_user_with_role(db, UUID(str(current_user.id)))
    if not user or not user.role:
        raise HTTPException(status_code=404, detail="User or role not found")
    return [user.role.name]


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Authenticate user with email and password."""
    try:
        return await login_user(
            db=db,
            email=login_request.email,
            password=login_request.password,
            response=response
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic message
        # TODO: Add proper logging
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login service temporarily unavailable"
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


@router.post("/refresh", response_model=SimpleRefreshResponse)
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> SimpleRefreshResponse:
    """Refresh access token using refresh token from cookie or request body."""
    try:
        # Get refresh token from cookie or request body
        token_to_refresh = None

        if refresh_token:
            # Cookie-based refresh (preferred)
            token_to_refresh = refresh_token

        if not token_to_refresh:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required in cookie or request body"
            )

        refresh_response = await refresh_user_tokens(token_to_refresh, db)

        # Set new cookies if response object available and token came from cookie
        if refresh_token:
            # Environment-specific cookie settings
            is_production = settings.ENVIRONMENT == "production"
            cookie_domain = settings.COOKIE_DOMAIN if is_production else None
            cookie_secure = settings.COOKIE_SECURE if is_production else False
            cookie_samesite = settings.COOKIE_SAMESITE

            # Set new access token cookie
            response.set_cookie(
                key="access_token",
                value=refresh_response.access_token,
                max_age=settings.ACCESS_TOKEN_COOKIE_MAX_AGE,
                httponly=settings.COOKIE_HTTPONLY,
                secure=cookie_secure,
                samesite=cookie_samesite,
                domain=cookie_domain
            )

            # Set new refresh token cookie
            response.set_cookie(
                key="refresh_token",
                value=refresh_response.refresh_token,
                max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
                httponly=settings.COOKIE_HTTPONLY,
                secure=cookie_secure,
                samesite=cookie_samesite,
                domain=cookie_domain
            )

        return SimpleRefreshResponse(message="Tokens refreshed successfully")

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
    response: Response,
    # Cookie tokens
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db)
):
    """Logout the user by invalidating their tokens and clearing cookies."""
    try:
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
        # Environment-specific cookie settings
        is_production = settings.ENVIRONMENT == "production"
        cookie_domain = settings.COOKIE_DOMAIN if is_production else None
        cookie_samesite = settings.COOKIE_SAMESITE

        # Clear access token cookie
        response.set_cookie(
            key="access_token",
            value="",
            max_age=0,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE if is_production else False,
            samesite=cookie_samesite,
            domain=cookie_domain
        )

        # Clear refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value="",
            max_age=0,
            httponly=settings.COOKIE_HTTPONLY,
            secure=settings.COOKIE_SECURE if is_production else False,
            samesite=cookie_samesite,
            domain=cookie_domain
        )

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


@router.get("/roles", response_model=List[UserRoleSchema], tags=["admin"])
async def list_all_roles(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[UserRoleSchema]:
    """List all available user roles (admin only)."""
    roles = await get_all_roles(db)
    return [UserRoleSchema.model_validate(role) for role in roles]


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionSchema], tags=["admin"])
async def get_role_default_permissions(
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[PermissionSchema]:
    """Get default permissions for a specific role (admin only)."""
    # For now, return empty list as permissions are assigned individually
    # This could be extended to show recommended permissions per role
    return []
