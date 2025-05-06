from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from src.models.feature import Feature
from src.models.action import Action
from src.models.permission import Permission
from src.models.api_key_permission import APIKeyPermission
from src.auth.enums.actions import Actions
from src.auth.enums.features import Features


async def check_api_key_permissions(
    db: AsyncSession,
    api_key_id: UUID,
    feature: Features,
    action: Actions
) -> bool:
    """
    Check if an API key has permission to perform an action on a feature.

    Args:
        db: Database session
        api_key_id: UUID of the API key
        feature: Feature to check permission for
        action: Action to check permission for

    Returns:
        True if the API key has permission, False otherwise
    """
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

    # Check if API key has this permission
    api_key_permission_query = await db.execute(
        select(APIKeyPermission).where(
            APIKeyPermission.api_key_id == api_key_id,
            APIKeyPermission.permission_id == permission.id
        )
    )

    api_key_permission = api_key_permission_query.scalars().first()

    return api_key_permission is not None
