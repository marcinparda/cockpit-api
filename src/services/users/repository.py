"""User repository for database operations."""

from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, delete

from src.services.users.models import User
from src.services.authorization.roles.models import UserRole
from src.services.authorization.user_permissions.models import UserPermission
from src.services.authorization.permissions.models import Permission


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> Sequence[User]:
    """Get all users with role information."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


async def save_user(db: AsyncSession, user: User) -> User:
    """Save user to database."""
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User) -> User:
    """Update user in database."""
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user_record(db: AsyncSession, user: User) -> None:
    """Delete user record from database."""
    await db.delete(user)
    await db.commit()


async def get_role_by_id(db: AsyncSession, role_id: UUID) -> Optional[UserRole]:
    """Get role by ID."""
    result = await db.execute(
        select(UserRole).where(UserRole.id == role_id)
    )
    return result.scalars().first()


async def get_permissions_by_ids(db: AsyncSession, permission_ids: List[UUID]) -> Sequence[Permission]:
    """Get permissions by IDs."""
    result = await db.execute(
        select(Permission).where(Permission.id.in_(permission_ids))
    )
    return result.scalars().all()


async def get_existing_user_permissions(
    db: AsyncSession,
    user_id: UUID,
    permission_ids: List[UUID]
) -> Sequence[UserPermission]:
    """Get existing user permissions for given permission IDs."""
    result = await db.execute(
        select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id.in_(permission_ids)
            )
        )
    )
    return result.scalars().all()


async def save_user_permissions(
    db: AsyncSession,
    user_permissions: List[UserPermission]
) -> List[UserPermission]:
    """Save user permission assignments to database."""
    for user_permission in user_permissions:
        db.add(user_permission)

    await db.commit()

    for user_permission in user_permissions:
        await db.refresh(user_permission)

    return user_permissions


async def delete_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> int:
    """Delete user permission assignment. Returns number of deleted rows."""
    result = await db.execute(
        delete(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id
            )
        )
    )

    await db.commit()
    return result.rowcount


async def refresh_user_with_role(db: AsyncSession, user: User) -> User:
    """Refresh user with role relationship loaded."""
    await db.refresh(user, ["role"])
    return user
