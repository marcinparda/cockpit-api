from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.todos.collaborators.models import TodoProjectCollaborator
from src.services.todos.collaborators import repository
from src.services.todos.collaborators.schemas import TodoProjectCollaboratorResponse
from src.services.users.models import User
from src.services.todos.projects import service as projects_service


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


async def add_collaborators_to_project(
    db: AsyncSession,
    project_id: int,
    collaborators_data: List[dict],
    current_user_id: UUID
) -> List[TodoProjectCollaboratorResponse]:
    """Add collaborators to a project with all validation."""
    # Check ownership
    is_owner = await projects_service.is_user_project_owner(
        db, project_id, current_user_id
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    project = await projects_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    if not collaborators_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No collaborators provided"
        )

    collaborator_ids = [UUID(str(c["id"])) for c in collaborators_data]

    unique_ids, errors, users_found = await validate_collaborators_batch(
        db=db,
        project_id=project_id,
        user_ids=collaborator_ids,
        owner_id=UUID(str(project.owner_id)),
    )

    if any(errors.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "One or more collaborators are invalid", **errors},
        )

    await create_collaborators(db=db, project_id=project_id, user_ids=unique_ids)

    return build_collaborator_responses_from_users(users_found, unique_ids)


async def list_collaborators_for_project(
    db: AsyncSession,
    project_id: int,
    current_user_id: UUID
) -> List[TodoProjectCollaboratorResponse]:
    """List collaborators for a project with access check."""
    # Check access
    has_access = await projects_service.can_user_access_project(
        db, project_id, current_user_id
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    return await list_project_collaborators(db, project_id)


async def remove_collaborator_from_project(
    db: AsyncSession,
    project_id: int,
    user_id: UUID,
    current_user_id: UUID
) -> None:
    """Remove a collaborator from a project with validation."""
    # Check ownership
    is_owner = await projects_service.is_user_project_owner(
        db, project_id, current_user_id
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    user_obj = await projects_service.get_user_by_id(db, user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    collaborator = await get_collaborator_by_project_and_user(
        db, project_id, UUID(str(user_obj.id))
    )

    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    await repository.delete_collaborator(db, collaborator)
