"""User permission management business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from uuid import UUID

from src.services.authorization.user_permissions.models import UserPermission
from src.services.authorization.user_permissions import repository


async def get_user_permissions_by_user_id(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[UserPermission]:
    """Get all user permissions for a specific user."""
    return await repository.get_user_permissions_by_user_id(db, user_id)


async def get_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> UserPermission | None:
    """Get a specific user permission."""
    return await repository.get_user_permission(db, user_id, permission_id)


async def create_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> UserPermission:
    """Create a new user permission."""
    user_permission = UserPermission(
        user_id=user_id,
        permission_id=permission_id
    )
    return await repository.create_user_permission(db, user_permission)


async def delete_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> bool:
    """Delete a user permission. Returns True if deleted, False if not found."""
    user_permission = await repository.get_user_permission(db, user_id, permission_id)
    if user_permission:
        await repository.delete_user_permission(db, user_permission)
        return True
    return False
