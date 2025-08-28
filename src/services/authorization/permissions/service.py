"""Permission system business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Sequence
from uuid import UUID

from src.services.authorization.permissions.models import Feature, Action, Permission
from src.services.authorization.user_permissions.models import UserPermission
from src.services.users.models import User
from src.services.authorization.permissions.enums import Actions, Features
from src.services.authorization.roles.enums import Roles


async def get_feature_by_name(db: AsyncSession, feature_name: str) -> Feature | None:
    """Get a feature by its name."""
    result = await db.execute(select(Feature).where(Feature.name == feature_name))
    return result.scalars().first()


async def get_action_by_name(db: AsyncSession, action_name: str) -> Action | None:
    """Get an action by its name."""
    result = await db.execute(select(Action).where(Action.name == action_name))
    return result.scalars().first()


async def get_permission_by_feature_action(
    db: AsyncSession,
    feature_id: UUID,
    action_id: UUID
) -> Permission | None:
    """Get a permission by feature and action IDs."""
    result = await db.execute(
        select(Permission).where(
            Permission.feature_id == feature_id,
            Permission.action_id == action_id
        )
    )
    return result.scalars().first()


async def get_all_permissions(db: AsyncSession) -> Sequence[Permission]:
    """Get all permissions."""
    result = await db.execute(select(Permission))
    return result.scalars().all()


async def get_all_features(db: AsyncSession) -> Sequence[Feature]:
    """Get all features."""
    result = await db.execute(select(Feature))
    return result.scalars().all()


async def get_all_actions(db: AsyncSession) -> Sequence[Action]:
    """Get all actions."""
    result = await db.execute(select(Action))
    return result.scalars().all()


# TODO: Divide into smaller functions
async def has_user_permission(
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
    user_query = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_query.scalars().first()

    if not user or user.is_active is False:
        return []

    if user.role and user.role.name == Roles.ADMIN.value:
        return await get_admin_permissions(db)

    result = await db.execute(
        select(Permission)
        .join(UserPermission)
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()


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
