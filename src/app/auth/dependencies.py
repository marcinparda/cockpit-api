from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db
from src.app.auth.models import User
from src.app.auth.enums.actions import Actions
from src.app.auth.enums.features import Features
from src.app.auth.enums.roles import Roles
from src.app.auth.permissions import check_user_permissions
from src.app.auth.jwt_dependencies import get_current_active_user


async def require_admin_role(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to ensure current user has admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if user has admin role

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.role or current_user.role.name != Roles.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    return current_user


async def require_user_permissions(
    feature: Features,
    action: Actions,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to check if the current user has the required permission.

    Args:
        feature: Feature to check permission for
        action: Action to check permission for
        current_user: Current authenticated user
        db: Database session

    Returns:
        User object if user has permission

    Raises:
        HTTPException: If user doesn't have permission
    """
    # Admin users have all permissions
    if current_user.role and current_user.role.name == Roles.ADMIN.value:
        return current_user

    # Check specific permission for non-admin users
    has_permission = await check_user_permissions(
        db,
        UUID(str(current_user.id)),
        feature,
        action
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to {action.value} {feature.value}"
        )

    return current_user
