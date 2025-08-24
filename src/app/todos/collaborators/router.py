from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db
from src.app.todos.collaborators.schemas import (
    TodoProjectCollaboratorCreate,
    TodoProjectCollaboratorResponse,
)
from src.app.auth.models import User
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_categories_permissions
from src.app.auth.jwt_dependencies import get_current_active_user
from src.services.todo_access_service import can_user_access_project, user_is_project_owner
from src.app.todos.collaborators.service import (
    validate_collaborators_batch,
    create_collaborators,
    build_collaborator_responses_from_users,
    list_project_collaborators,
    get_collaborator_by_project_and_user,
)
from src.app.todos.projects.service import get_user_by_id
from src.app.todos.projects.models import TodoProject

router = APIRouter()


@router.post(
    "",
    response_model=list[TodoProjectCollaboratorResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_collaborators(
    collaborators: list[TodoProjectCollaboratorCreate],
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    """Add a list of collaborators to a todo project atomically."""
    # Check ownership
    is_owner = await user_is_project_owner(
        db, project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    project = await db.get(TodoProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    if not collaborators:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No collaborators provided"
        )

    collaborator_ids = [c.id for c in collaborators]

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

    service_responses = build_collaborator_responses_from_users(
        users_found, unique_ids)
    return [
        TodoProjectCollaboratorResponse.model_validate(r.model_dump())
        for r in service_responses
    ]


@router.get(
    "",
    response_model=list[TodoProjectCollaboratorResponse],
)
async def list_collaborators(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """List all collaborators for a todo project."""
    # Check access
    has_access = await can_user_access_project(
        db, project_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    service_responses = await list_project_collaborators(db, project_id)
    return [
        TodoProjectCollaboratorResponse.model_validate(r.model_dump())
        for r in service_responses
    ]


@router.delete("/{user_id}", status_code=204)
async def remove_collaborator(
    user_id: UUID,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    """Remove a collaborator from a todo project."""
    # Check ownership
    is_owner = await user_is_project_owner(
        db, project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    user_obj = await get_user_by_id(db, user_id)
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

    await db.delete(collaborator)
    await db.commit()
