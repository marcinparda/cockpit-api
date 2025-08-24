from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.todos.collaborators.models import TodoProjectCollaborator
from src.app.todos.collaborators import repository
from src.app.todos.collaborators.schemas import TodoProjectCollaboratorResponse
from src.app.auth.models import User


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
    users_found = await repository.get_users_by_ids(db, unique_ids)
    found_ids = {u.id for u in users_found}

    # Compute errors
    missing_ids = [str(uid) for uid in unique_ids if uid not in found_ids]
    owner_included = [str(uid) for uid in unique_ids if uid == owner_id]

    # Existing collaborators in this project
    existing_ids = await repository.get_existing_collaborator_user_ids(db, project_id, unique_ids)
    existing_ids = [UUID(str(e)) for e in existing_ids]

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
    return await repository.create_collaborators(db, project_id, user_ids)


def build_collaborator_responses_from_users(
    users: Sequence[User], user_ids: Sequence[UUID]
) -> List[TodoProjectCollaboratorResponse]:
    """Build response models preserving the order of user_ids."""
    users_by_id = {str(u.id): u for u in users}
    return [
        TodoProjectCollaboratorResponse(
            email=str(users_by_id[str(user_id)].email),
            id=user_id,
        )
        for user_id in user_ids
    ]


async def list_project_collaborators(
    db: AsyncSession, project_id: int
) -> List[TodoProjectCollaboratorResponse]:
    """Return all collaborators for a project as response models."""
    user_ids = await repository.list_project_collaborator_user_ids(db, project_id)
    if not user_ids:
        return []

    users = await repository.get_users_by_ids(db, user_ids)

    return [
        TodoProjectCollaboratorResponse(
            email=str(user.email),
            id=UUID(str(user.id)),
        )
        for user in users
    ]


async def get_collaborator_by_project_and_user(
    db: AsyncSession, project_id: int, user_id: UUID
) -> Optional[TodoProjectCollaborator]:
    return await repository.get_collaborator_by_project_and_user(db, project_id, user_id)


async def get_collaborator_emails(db: AsyncSession, project_id: int) -> List[str]:
    return await repository.get_collaborator_emails(db, project_id)
