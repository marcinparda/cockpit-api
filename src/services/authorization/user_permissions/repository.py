"""User permission database repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import Sequence
from uuid import UUID

from src.services.authorization.user_permissions.models import UserPermission


async def get_user_permissions_by_user_id(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[UserPermission]:
    """Get all user permissions for a specific user."""
    result = await db.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
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


async def create_user_permission(
    db: AsyncSession,
    user_permission: UserPermission
) -> UserPermission:
    """Create a new user permission."""
    db.add(user_permission)
    await db.commit()
    await db.refresh(user_permission)
    return user_permission


async def delete_user_permission(
    db: AsyncSession,
    user_permission: UserPermission
) -> None:
    """Delete a user permission."""
    await db.delete(user_permission)
    await db.commit()
