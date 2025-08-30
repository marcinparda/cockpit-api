"""User permission management business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from uuid import UUID

from src.services.authorization.user_permissions.models import UserPermission
from src.services.authorization.user_permissions import repository
from src.services.authorization.permissions.models import Permission


async def get_user_permissions(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[Permission]:
    """Get all user permissions for a specific user."""
    return await repository.get_permissions_by_user_id(db, user_id)


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


async def get_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> UserPermission | None:
    return await repository.get_user_permission(db, user_id, permission_id)
