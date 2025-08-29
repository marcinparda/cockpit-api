"""Permission system business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from uuid import UUID

from src.services.authorization.permissions.models import Feature, Action, Permission
from src.services.authorization.permissions import repository
from src.services.authorization.permissions.enums import Actions, Features
from src.services.authorization.roles.enums import Roles


async def get_feature_by_name(db: AsyncSession, feature_name: str) -> Feature | None:
    """Get a feature by its name."""
    return await repository.get_feature_by_name(db, feature_name)


async def get_action_by_name(db: AsyncSession, action_name: str) -> Action | None:
    """Get an action by its name."""
    return await repository.get_action_by_name(db, action_name)


async def get_permission_by_feature_action(
    db: AsyncSession,
    feature_id: UUID,
    action_id: UUID
) -> Permission | None:
    """Get a permission by feature and action IDs."""
    return await repository.get_permission_by_feature_action(db, feature_id, action_id)


async def get_all_permissions(db: AsyncSession) -> Sequence[Permission]:
    """Get all permissions."""
    return await repository.get_all_permissions(db)


async def get_all_features(db: AsyncSession) -> Sequence[Feature]:
    """Get all features."""
    return await repository.get_all_features(db)


async def get_all_actions(db: AsyncSession) -> Sequence[Action]:
    """Get all actions."""
    return await repository.get_all_actions(db)


# TODO: Divide into smaller functions
async def has_user_permission(
    db: AsyncSession,
    user_id: UUID,
    feature: Features,
    action: Actions
) -> bool:
    """Check if a current user has permission to perform an action on a feature."""
    user = await repository.get_user_by_id(db, user_id)

    if not user or user.is_active is False:
        return False

    # Admin users have all permissions
    if user.role and user.role.name == Roles.ADMIN.value:
        return True

    # Get feature and action IDs
    feature_obj = await repository.get_feature_by_name(db, feature.value)
    if not feature_obj:
        return False

    action_obj = await repository.get_action_by_name(db, action.value)
    if not action_obj:
        return False

    # Find the permission ID
    permission = await repository.get_permission_by_feature_action(
        db, feature_obj.id, action_obj.id
    )
    if not permission:
        return False

    # Check if user has this permission
    user_permission = await repository.get_user_permission_by_user_and_permission(
        db, user_id, permission.id
    )

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
    user = await repository.get_user_by_id(db, user_id)

    if not user or user.is_active is False:
        return []

    if user.role and user.role.name == Roles.ADMIN.value:
        return await get_admin_permissions(db)

    return await repository.get_permissions_by_user_id(db, user_id)


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
    return await repository.get_all_permissions(db)
