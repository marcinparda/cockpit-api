from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db
from src.services.todos.collaborators.schemas import (
    TodoProjectCollaboratorCreate,
    TodoProjectCollaboratorResponse,
)
from src.services.users.models import User
from src.services.authentication.dependencies import get_current_user
from src.services.todos.collaborators import service

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
    current_user: User = Depends(get_current_user),
):
    """Add a list of collaborators to a todo project atomically."""
    collaborators_data = [c.model_dump() for c in collaborators]
    return await service.add_collaborators_to_project(
        db=db,
        project_id=project_id,
        collaborators_data=collaborators_data,
        current_user_id=UUID(str(current_user.id))
    )


@router.get(
    "",
    response_model=list[TodoProjectCollaboratorResponse],
)
async def list_collaborators(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all collaborators for a todo project."""
    return await service.list_collaborators_for_project(
        db=db,
        project_id=project_id,
        current_user_id=UUID(str(current_user.id))
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_collaborator(
    user_id: UUID,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a collaborator from a todo project."""
    await service.remove_collaborator_from_project(
        db=db,
        project_id=project_id,
        user_id=user_id,
        current_user_id=UUID(str(current_user.id))
    )
