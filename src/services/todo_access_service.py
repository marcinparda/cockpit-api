"""Access control service for Todo app collaboration feature."""

from sqlalchemy import and_
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_

from src.models.todo_project import TodoProject
from src.models.todo_project_collaborator import TodoProjectCollaborator
from src.models.todo_item import TodoItem


async def user_can_access_project(db: AsyncSession, project_id: int, user_id: UUID) -> bool:
    """Check if a user can access a project (as owner or collaborator)."""
    # First check if user is the owner
    result = await db.execute(
        select(TodoProject).where(
            and_(
                TodoProject.id == project_id,
                TodoProject.owner_id == user_id
            )
        )
    )
    if result.scalars().first():
        return True

    # Then check if user is a collaborator
    result = await db.execute(
        select(TodoProjectCollaborator).where(
            and_(
                TodoProjectCollaborator.project_id == project_id,
                TodoProjectCollaborator.user_id == user_id
            )
        )
    )
    if result.scalars().first():
        return True

    return False


async def user_is_project_owner(db: AsyncSession, project_id: int, user_id: UUID) -> bool:
    """Check if a user is the owner of a project."""
    result = await db.execute(
        select(TodoProject).where(
            and_(
                TodoProject.id == project_id,
                TodoProject.owner_id == user_id
            )
        )
    )
    return result.scalars().first() is not None


async def is_general_project(db: AsyncSession, project_id: int) -> bool:
    """Check if a project is a General project."""
    result = await db.execute(
        select(TodoProject).where(
            and_(
                TodoProject.id == project_id,
                TodoProject.is_general == True
            )
        )
    )
    return result.scalars().first() is not None


async def user_can_access_item(db: AsyncSession, item_id: int, user_id: UUID) -> bool:
    """Check if a user can access a todo item (by having access to its project)."""
    # Get the item's project_id
    result = await db.execute(
        select(TodoItem.project_id).where(TodoItem.id == item_id)
    )
    project_id = result.scalar_one_or_none()

    if project_id is None:
        return False

    # Check if user can access the project
    return await user_can_access_project(db, project_id, user_id)


async def get_accessible_project_ids(db: AsyncSession, user_id: UUID) -> list[int]:
    """Get all project IDs that a user can access (owned or collaborated)."""
    # Get projects where user is owner
    result = await db.execute(
        select(TodoProject.id).where(TodoProject.owner_id == user_id)
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


async def user_can_access_project(
    db: AsyncSession,
    project_id: int,
    user_id: UUID
) -> bool:
    """
    Check if a user has access to a project (as owner or collaborator).

    Args:
        db: Database session
        project_id: ID of the project to check
        user_id: ID of the user

    Returns:
        True if user is owner or collaborator, False otherwise
    """
    # Check if user is the owner
    result = await db.execute(
        select(TodoProject)
        .where(and_(
            TodoProject.id == project_id,
            TodoProject.owner_id == user_id
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


async def user_can_access_item(
    db: AsyncSession,
    item_id: int,
    user_id: UUID
) -> bool:
    """
    Check if a user has access to an item (via project ownership or collaboration).

    Args:
        db: Database session
        item_id: ID of the item to check
        user_id: ID of the user

    Returns:
        True if user has access, False otherwise
    """
    # Get the item's project ID
    result = await db.execute(
        select(TodoItem.project_id)
        .where(TodoItem.id == item_id)
    )
    project_id = result.scalar()

    if not project_id:
        return False

    # Check access to the project
    return await user_can_access_project(db, project_id, user_id)


async def user_is_project_owner(
    db: AsyncSession,
    project_id: int,
    user_id: UUID
) -> bool:
    """
    Check if a user is the owner of a project.

    Args:
        db: Database session
        project_id: ID of the project to check
        user_id: ID of the user

    Returns:
        True if user is the owner, False otherwise
    """
    result = await db.execute(
        select(TodoProject)
        .where(and_(
            TodoProject.id == project_id,
            TodoProject.owner_id == user_id
        ))
    )
    return result.scalars().first() is not None


async def is_general_project(
    db: AsyncSession,
    project_id: int
) -> bool:
    """
    Check if a project is a "General" project.

    Args:
        db: Database session
        project_id: ID of the project to check

    Returns:
        True if project is a General project, False otherwise
    """
    result = await db.execute(
        select(TodoProject.is_general)
        .where(TodoProject.id == project_id)
    )
    return result.scalar() or False
