from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.todos.projects.models import TodoProject as TodoProjectModel
from src.services.todos.collaborators.models import TodoProjectCollaborator
from src.services.users.models import User
from datetime import datetime


async def list_projects_owned_by(db: AsyncSession, owner_id: UUID) -> List[TodoProjectModel]:
    res = await db.execute(
        select(TodoProjectModel).where(TodoProjectModel.owner_id == owner_id)
    )
    return list(res.scalars().all())


async def list_projects_collaborating_by(db: AsyncSession, user_id: UUID) -> List[TodoProjectModel]:
    res = await db.execute(
        select(TodoProjectModel)
        .join(TodoProjectCollaborator)
        .where(TodoProjectCollaborator.user_id == user_id)
    )
    return list(res.scalars().all())


async def get_owner_email(db: AsyncSession, owner_id: UUID) -> str:
    res = await db.execute(select(User.email).where(User.id == owner_id))
    return res.scalar_one()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalars().first()


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[TodoProjectModel]:
    """Get a project by its ID."""
    result = await db.execute(
        select(TodoProjectModel).where(TodoProjectModel.id == project_id)
    )
    return result.scalars().first()


async def create_project(db: AsyncSession, *, name: str, owner_id: UUID) -> TodoProjectModel:
    now = datetime.now()
    stmt = (
        insert(TodoProjectModel)
        .values(name=name, owner_id=owner_id, created_at=now, updated_at=now)
        .returning(TodoProjectModel)
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.scalar_one()


async def is_user_project_owner(
    db: AsyncSession,
    project_id: int,
    user_id: UUID
) -> bool:
    """Check if a user is the owner of a project."""
    result = await db.execute(
        select(TodoProjectModel)
        .where(and_(
            TodoProjectModel.id == project_id,
            TodoProjectModel.owner_id == user_id
        ))
    )
    return result.scalars().first() is not None


async def is_general_project(
    db: AsyncSession,
    project_id: int
) -> bool:
    """Check if a project is a General project."""
    result = await db.execute(
        select(TodoProjectModel.is_general)
        .where(TodoProjectModel.id == project_id)
    )
    return result.scalar() or False


async def get_accessible_project_ids(db: AsyncSession, user_id: UUID) -> List[int]:
    """Get all project IDs that a user can access (owned or collaborated)."""
    # Get projects where user is owner
    result = await db.execute(
        select(TodoProjectModel.id).where(TodoProjectModel.owner_id == user_id)
    )
    owned_project_ids = result.scalars().all()

    # Get projects where user is collaborator
    result = await db.execute(
        select(TodoProjectCollaborator.project_id).where(
            TodoProjectCollaborator.user_id == user_id
        )
    )
    collab_project_ids = result.scalars().all()

    # Combine and deduplicate
    all_project_ids = set(owned_project_ids) | set(collab_project_ids)
    return list(all_project_ids)


async def can_user_access_project(
    db: AsyncSession,
    project_id: int,
    user_id: UUID
) -> bool:
    """Check if a user has access to a project (as owner or collaborator)."""
    # Check if user is the owner
    result = await db.execute(
        select(TodoProjectModel)
        .where(and_(
            TodoProjectModel.id == project_id,
            TodoProjectModel.owner_id == user_id
        ))
    )
    project = result.scalars().first()

    if project:
        return True

    # Check if user is a collaborator
    result = await db.execute(
        select(TodoProjectCollaborator)
        .where(and_(
            TodoProjectCollaborator.project_id == project_id,
            TodoProjectCollaborator.user_id == user_id
        ))
    )
    collaborator = result.scalars().first()

    return collaborator is not None
