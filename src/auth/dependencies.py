from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from src.core.database import get_db
from src.models.api_key import APIKey
from src.models.user import User
from src.auth.enums.actions import Actions
from src.auth.enums.features import Features
from src.auth.enums.roles import Roles
from src.auth.permissions import check_api_key_permissions, check_user_permissions
from src.auth.jwt_dependencies import get_current_active_user
from src.services.user_service import check_user_permission

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )

    result = await db.execute(select(APIKey).where(APIKey.key == api_key, APIKey.is_active == True))
    api_key_obj = result.scalars().first()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    return api_key_obj


async def require_permissions(
    feature: Features,
    action: Actions,
    api_key: APIKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """Dependency to check if the API key has the required permission."""
    has_permission = await check_api_key_permissions(db, api_key.id.hex, feature, action)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key does not have permission to {action.value} {feature.value}"
        )

    return api_key


async def require_admin_role(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to ensure user has admin role.

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
    Dependency to check if the user has the required permission.

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
