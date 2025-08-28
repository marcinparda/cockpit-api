"""Permission system business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Sequence
from uuid import UUID

from src.services.authorization.permissions.models import Feature, Action, Permission


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
