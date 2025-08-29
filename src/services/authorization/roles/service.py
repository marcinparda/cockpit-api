"""Role management business logic."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from uuid import UUID

from src.services.authorization.roles.models import UserRole
from src.services.authorization.roles import repository


async def get_user_roles_by_id(db: AsyncSession, user_id: UUID) -> UserRole | None:
    """Get a role by its ID."""
    return await repository.get_user_roles_by_id(db, user_id)


async def get_role_by_id(db: AsyncSession, role_id: UUID) -> UserRole | None:
    """Get a role by its ID."""
    return await repository.get_role_by_id(db, role_id)


async def get_role_by_name(db: AsyncSession, role_name: str) -> UserRole | None:
    """Get a role by its name."""
    return await repository.get_role_by_name(db, role_name)


async def get_all_roles(db: AsyncSession) -> Sequence[UserRole]:
    """Get all roles."""
    return await repository.get_all_roles(db)
