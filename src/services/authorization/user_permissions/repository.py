"""User permission database repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from typing import Sequence, Optional
from uuid import UUID

from src.services.authorization.user_permissions.models import UserPermission
from src.services.authorization.permissions.models import Permission


async def get_user_permission_by_user_and_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> Optional[UserPermission]:
    """Get user permission by user ID and permission ID."""
    result = await db.execute(
        select(UserPermission).where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        )
    )
    return result.scalars().first()


async def get_permissions_by_user_id(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[Permission]:
    """Get all permissions for a user."""
    result = await db.execute(
        select(Permission)
        .join(UserPermission)
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()


async def get_user_permissions(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[UserPermission]:
    """Get all user permissions for a specific user."""
    result = await db.execute(
        select(UserPermission)
        .options(joinedload(UserPermission.permission))
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()


async def get_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> UserPermission | None:
    """Get a specific user permission."""
    result = await db.execute(
        select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id
            )
        )
    )
    return result.scalars().first()


async def delete_user_permission(
    db: AsyncSession,
    user_permission: UserPermission
) -> None:
    """Delete a user permission."""
    await db.delete(user_permission)
    await db.commit()
