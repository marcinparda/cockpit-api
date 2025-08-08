from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime
from uuid import UUID

from src.core.database import get_db
from src.models.todo_project import TodoProject as TodoProjectModel
from src.models.todo_project_collaborator import TodoProjectCollaborator
from src.models.user import User
from src.schemas.todo_project import (
    TodoProject, TodoProjectCreate, TodoProjectUpdate,
    TodoProjectCollaboratorCreate, TodoProjectCollaboratorResponse
)
from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_categories_permissions
from src.auth.jwt_dependencies import get_current_active_user
from src.services.todo_access_service import user_can_access_project, is_general_project

router = APIRouter()


@router.get("", response_model=list[TodoProject])
async def list_todo_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """List all todo projects the user owns or collaborates on."""
    # Get projects where user is owner
    result = await db.execute(
        select(TodoProjectModel).where(
            TodoProjectModel.owner_id == UUID(str(current_user.id))
        )
    )
    owned_projects = result.scalars().all()

    # Get projects where user is collaborator
    result = await db.execute(
        select(TodoProjectModel)
        .join(TodoProjectCollaborator)
        .where(TodoProjectCollaborator.user_id == UUID(str(current_user.id)))
    )
    collab_projects = result.scalars().all()

    # Combine and deduplicate
    all_projects = {p.id: p for p in owned_projects}
    for p in collab_projects:
        if p.id not in all_projects:
            all_projects[p.id] = p

    # Manually create TodoProject objects to avoid async relationship issues
    projects_list = []
    for project in all_projects.values():
        # Fetch collaborators manually for each project
        result = await db.execute(
            select(TodoProjectCollaborator).where(
                TodoProjectCollaborator.project_id == project.id
            )
        )
        collaborators = result.scalars().all()

        emails = []
        for collab in collaborators:
            user = await db.get(User, collab.user_id)
            if user:
                emails.append(user.email)

        project_dict = {
            "id": project.id,
            "name": project.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "owner_id": project.owner_id,
            "is_general": project.is_general,
            "collaborators": emails
        }
        projects_list.append(project_dict)

    return projects_list


@router.post("", response_model=TodoProject, status_code=status.HTTP_201_CREATED)
async def create_todo_project(
    todo_project: TodoProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.CREATE))
):
    """Create a new todo project owned by the current user."""
    now = datetime.now()
    db_todo_project = TodoProjectModel(
        **todo_project.dict(),
        created_at=now,
        updated_at=now,
        owner_id=UUID(str(current_user.id)),
        is_general=False
    )
    db.add(db_todo_project)
    await db.commit()
    await db.refresh(db_todo_project)

    project_dict = {
        "id": db_todo_project.id,
        "name": db_todo_project.name,
        "created_at": db_todo_project.created_at,
        "updated_at": db_todo_project.updated_at,
        "owner_id": db_todo_project.owner_id,
        "is_general": db_todo_project.is_general,
        "collaborators": []
    }
    return project_dict


@router.get("/{todo_project_id}", response_model=TodoProject)
async def get_todo_project(
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """Get a specific todo project if the user has access."""
    # Check access
    from src.services.todo_access_service import user_can_access_project
    has_access = await user_can_access_project(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    # Fetch collaborators manually
    result = await db.execute(
        select(TodoProjectCollaborator).where(
            TodoProjectCollaborator.project_id == todo_project_id
        )
    )
    collaborators = result.scalars().all()

    emails = []
    for collab in collaborators:
        user = await db.get(User, collab.user_id)
        if user:
            emails.append(user.email)

    project_dict = {
        "id": todo_project.id,
        "name": todo_project.name,
        "created_at": todo_project.created_at,
        "updated_at": todo_project.updated_at,
        "owner_id": todo_project.owner_id,
        "is_general": todo_project.is_general,
        "collaborators": emails
    }
    return project_dict


@router.put("/{todo_project_id}", response_model=TodoProject)
async def update_todo_project(
    todo_project_update: TodoProjectUpdate,
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    """Update a todo project if the user has access and it's not a General project."""
    has_access = await user_can_access_project(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    # Check if General project
    is_general = await is_general_project(db, todo_project_id)
    if is_general:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The General project cannot be modified or deleted"
        )

    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    for key, value in todo_project_update.dict(exclude_unset=True).items():
        setattr(todo_project, key, value)

    todo_project.updated_at = datetime.now()
    await db.commit()
    await db.refresh(todo_project)

    result = await db.execute(
        select(TodoProjectCollaborator).where(
            TodoProjectCollaborator.project_id == todo_project_id
        )
    )
    collaborators = result.scalars().all()

    emails = []
    for collab in collaborators:
        user = await db.get(User, collab.user_id)
        if user:
            emails.append(user.email)

    project_dict = {
        "id": todo_project.id,
        "name": todo_project.name,
        "created_at": todo_project.created_at,
        "updated_at": todo_project.updated_at,
        "owner_id": todo_project.owner_id,
        "is_general": todo_project.is_general,
        "collaborators": emails
    }
    return project_dict


@router.delete("/{todo_project_id}", status_code=204)
async def delete_todo_project(
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    """Delete a todo project if the user is the owner and it's not a General project."""
    # Check ownership
    from src.services.todo_access_service import user_is_project_owner, is_general_project
    is_owner = await user_is_project_owner(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    # Check if General project
    is_general = await is_general_project(db, todo_project_id)
    if is_general:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The General project cannot be modified or deleted"
        )

    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    await db.delete(todo_project)
    await db.commit()


# Collaborator Management Endpoints

@router.post("/{todo_project_id}/collaborators", response_model=TodoProjectCollaboratorResponse, status_code=status.HTTP_201_CREATED)
async def add_collaborator(
    collaborator_data: TodoProjectCollaboratorCreate,
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    """Add a collaborator to a todo project."""
    # Check ownership
    from src.services.todo_access_service import user_is_project_owner
    is_owner = await user_is_project_owner(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    # Check if project exists
    project = await db.get(TodoProjectModel, todo_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    user = await db.execute(select(User).where(User.id == collaborator_data.id))
    user_obj = user.scalars().first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    if user_obj.id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already the project owner"
        )

    result = await db.execute(
        select(TodoProjectCollaborator).where(
            and_(
                TodoProjectCollaborator.project_id == todo_project_id,
                TodoProjectCollaborator.user_id == user_obj.id
            )
        )
    )
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a collaborator on this project"
        )

    now = datetime.now()
    db_collaborator = TodoProjectCollaborator(
        project_id=todo_project_id,
        user_id=user_obj.id,
        created_at=now,
        updated_at=now
    )

    db.add(db_collaborator)
    await db.commit()
    await db.refresh(db_collaborator)

    return TodoProjectCollaboratorResponse(email=str(user_obj.email))


@router.get("/{todo_project_id}/collaborators", response_model=list[TodoProjectCollaboratorResponse])
async def list_collaborators(
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """List all collaborators for a todo project."""
    # Check access
    from src.services.todo_access_service import user_can_access_project
    has_access = await user_can_access_project(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    result = await db.execute(
        select(TodoProjectCollaborator).where(
            TodoProjectCollaborator.project_id == todo_project_id
        )
    )
    collaborators = result.scalars().all()
    collaborator_responses = []
    for collab in collaborators:
        user = await db.get(User, collab.user_id)
        if user:
            collaborator_responses.append(
                TodoProjectCollaboratorResponse(email=str(user.email))
            )
    return collaborator_responses


@router.delete("/{todo_project_id}/collaborators/{user_id}", status_code=204)
async def remove_collaborator(
    user_id: UUID,
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    """Remove a collaborator from a todo project."""
    # Check ownership
    from src.services.todo_access_service import user_is_project_owner
    is_owner = await user_is_project_owner(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    user = await db.execute(select(User).where(User.id == user_id))
    user_obj = user.scalars().first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(TodoProjectCollaborator).where(
            and_(
                TodoProjectCollaborator.project_id == todo_project_id,
                TodoProjectCollaborator.user_id == user_obj.id
            )
        )
    )
    collaborator = result.scalars().first()

    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborator not found"
        )

    await db.delete(collaborator)
    await db.commit()
