"""Permissions repository for database operations."""

from typing import Sequence, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services.authorization.permissions.models import Feature, Action, Permission


async def get_feature_by_name(db: AsyncSession, feature_name: str) -> Optional[Feature]:
    """Get a feature by its name."""
    result = await db.execute(select(Feature).where(Feature.name == feature_name))
    return result.scalars().first()


async def get_action_by_name(db: AsyncSession, action_name: str) -> Optional[Action]:
    """Get an action by its name."""
    result = await db.execute(select(Action).where(Action.name == action_name))
    return result.scalars().first()


async def get_permission_by_feature_action(
    db: AsyncSession,
    feature_id: UUID,
    action_id: UUID
) -> Optional[Permission]:
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
    result = await db.execute(
        select(Permission)
        .options(selectinload(Permission.feature), selectinload(Permission.action))
    )
    return result.scalars().all()


# async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
#     """Get user by ID."""
#     result = await db.execute(select(User).where(User.id == user_id))
#     return result.scalars().first()


# async def get_user_permission_by_user_and_permission(
#     db: AsyncSession,
#     user_id: UUID,
#     permission_id: UUID
# ) -> Optional[UserPermission]:
#     """Get user permission by user ID and permission ID."""
#     result = await db.execute(
#         select(UserPermission).where(
#             UserPermission.user_id == user_id,
#             UserPermission.permission_id == permission_id
#         )
#     )
#     return result.scalars().first()


# async def get_permissions_by_user_id(
#     db: AsyncSession,
#     user_id: UUID
# ) -> Sequence[Permission]:
#     """Get all permissions for a user."""
#     result = await db.execute(
#         select(Permission)
#         .join(UserPermission)
#         .where(UserPermission.user_id == user_id)
#     )
#     return result.scalars().all()
