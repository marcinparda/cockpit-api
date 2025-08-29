"""Role repository for database operations."""

from typing import Sequence, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.services.authorization.roles.models import UserRole


async def get_role_by_id(db: AsyncSession, role_id: UUID) -> Optional[UserRole]:
    """Get a role by its ID."""
    result = await db.execute(select(UserRole).where(UserRole.id == role_id))
    return result.scalars().first()


async def get_role_by_name(db: AsyncSession, role_name: str) -> Optional[UserRole]:
    """Get a role by its name."""
    result = await db.execute(select(UserRole).where(UserRole.name == role_name))
    return result.scalars().first()


async def get_all_roles(db: AsyncSession) -> Sequence[UserRole]:
    """Get all roles."""
    result = await db.execute(select(UserRole))
    return result.scalars().all()
