"""FastAPI dependencies for authorization domain services."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db
from src.services.users.models import User

from src.services.authorization.permissions.enums import Actions, Features
from src.services.authorization.roles.enums import Roles
from src.services.authorization.shared.access_control_service import has_user_permissions
from src.services.authentication.shared.dependencies import get_current_user


def require_permission(feature: Features, action: Actions):
    """
    Factory function that returns a dependency to check if user has specific permission.

    Args: 
        feature: Feature to check permission for
        action: Action to check permission for

    Returns:
        Dependency function that validates user permission
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Check if the current user has the required permission.

        Args:
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
        has_permission = await has_user_permissions(
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

    return permission_checker


async def require_admin_role(
    current_user: User = Depends(get_current_user),
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
