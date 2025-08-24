from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Sequence

from src.app.auth.models import Feature
from src.app.auth.models import Action
from src.app.auth.models import Permission
from src.app.auth.models import User
from src.app.auth.models import UserPermission
from src.app.auth.enums.actions import Actions
from src.app.auth.enums.features import Features
from src.app.auth.enums.roles import Roles


async def check_user_permissions(
    db: AsyncSession,
    user_id: UUID,
    feature: Features,
    action: Actions
) -> bool:
    """
    Check if a current user has permission to perform an action on a feature.

    Args:
        db: Database session
        user_id: UUID of the user
        feature: Feature to check permission for
        action: Action to check permission for

    Returns:
        True if the user has permission, False otherwise
    """
    # Get user with role
    user_query = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_query.scalars().first()

    if not user or user.is_active is False:
        return False

    # Admin users have all permissions
    if user.role and user.role.name == Roles.ADMIN.value:
        return True

    # Get feature and action IDs
    feature_query = await db.execute(select(Feature).where(Feature.name == feature.value))
    feature_obj = feature_query.scalars().first()

    if not feature_obj:
        return False

    action_query = await db.execute(select(Action).where(Action.name == action.value))
    action_obj = action_query.scalars().first()

    if not action_obj:
        return False

    # Find the permission ID
    permission_query = await db.execute(
        select(Permission).where(
            Permission.feature_id == feature_obj.id,
            Permission.action_id == action_obj.id
        )
    )
    permission = permission_query.scalars().first()

    if not permission:
        return False

    # Check if user has this permission
    user_permission_query = await db.execute(
        select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission.id
        )
    )

    user_permission = user_permission_query.scalars().first()

    return user_permission is not None


async def get_user_permissions(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[Permission]:
    """
    Get all permissions for a user.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        Sequence of Permission objects
    """
    # Get user with role
    user_query = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_query.scalars().first()

    if not user or user.is_active is False:
        return []

    # Admin users have all permissions
    if user.role and user.role.name == Roles.ADMIN.value:
        return await get_admin_permissions(db)

    # Get user-specific permissions
    result = await db.execute(
        select(Permission)
        .join(UserPermission)
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()


async def user_has_admin_role(
    db: AsyncSession,
    user_id: UUID
) -> bool:
    """
    Check if user has admin role.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        True if user has admin role, False otherwise
    """
    user_query = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_query.scalars().first()

    return bool(user and user.role and user.role.name == Roles.ADMIN.value)


async def get_admin_permissions(
    db: AsyncSession
) -> Sequence[Permission]:
    """
    Get all permissions for admin role.

    Args:
        db: Database session

    Returns:
        Sequence of all Permission objects
    """
    result = await db.execute(select(Permission))
    return result.scalars().all()
