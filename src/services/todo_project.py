from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.todo_project_collaborator import TodoProjectCollaborator
from src.models.user import User
from src.schemas.todo_project import TodoProjectCollaboratorResponse


async def validate_collaborators_batch(
    db: AsyncSession,
    project_id: int,
    user_ids: Iterable[UUID],
    owner_id: UUID,
) -> Tuple[List[UUID], dict, List[User]]:
    """
    Validate a batch of collaborator user IDs for a project.

    Returns a tuple of:
      - unique_ids: de-duplicated list of UUIDs to add
      - errors: dict with keys 'missing_user_ids', 'already_collaborators', 'owner_ids'
      - users_found: list of User objects found for the provided IDs
    """
    # Deduplicate and normalize UUIDs
    unique_ids = list({UUID(str(uid)) for uid in user_ids})

    # Fetch users
    result = await db.execute(select(User).where(User.id.in_(unique_ids)))
    users_found: List[User] = list(result.scalars().all())
    found_ids = {u.id for u in users_found}

    # Compute errors
    missing_ids = [str(uid) for uid in unique_ids if uid not in found_ids]
    owner_included = [str(uid) for uid in unique_ids if uid == owner_id]

    # Existing collaborators in this project
    result = await db.execute(
        select(TodoProjectCollaborator).where(
            and_(
                TodoProjectCollaborator.project_id == project_id,
                TodoProjectCollaborator.user_id.in_(unique_ids),
            )
        )
    )
    existing = list(result.scalars().all())
    existing_ids = [str(e.user_id) for e in existing]

    errors = {
        "missing_user_ids": missing_ids,
        "already_collaborators": existing_ids,
        "owner_ids": owner_included,
    }
    return unique_ids, errors, users_found


async def create_collaborators(
    db: AsyncSession,
    project_id: int,
    user_ids: Sequence[UUID],
) -> None:
    """Create collaborators for a project in a single transaction."""
    now = datetime.now()
    to_create = [
        TodoProjectCollaborator(
            project_id=project_id,
            user_id=uid,
            created_at=now,
            updated_at=now,
        )
        for uid in user_ids
    ]

    db.add_all(to_create)
    await db.commit()


def build_collaborator_responses_from_users(
    users: Sequence[User], user_ids: Sequence[UUID]
) -> List[TodoProjectCollaboratorResponse]:
    """Build response models preserving the order of user_ids."""
    users_by_id = {str(u.id): u for u in users}
    return [
        TodoProjectCollaboratorResponse(
            email=str(users_by_id[str(uid)].email),
            id=UUID(str(uid)),
        )
        for uid in user_ids
    ]


async def list_project_collaborators(
    db: AsyncSession, project_id: int
) -> List[TodoProjectCollaboratorResponse]:
    """Return all collaborators for a project as response models."""
    # Get all user IDs for the project
    result = await db.execute(
        select(TodoProjectCollaborator.user_id).where(
            TodoProjectCollaborator.project_id == project_id
        )
    )
    user_ids: List[UUID] = list(result.scalars().all())
    if not user_ids:
        return []

    # Fetch users in one query
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users: List[User] = list(users_result.scalars().all())

    return build_collaborator_responses_from_users(users, user_ids)
