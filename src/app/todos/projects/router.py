from fastapi import APIRouter, Depends, status, HTTPException, Path
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID

from src.core.database import get_db
from src.app.todos.projects.models import TodoProject as TodoProjectModel
from src.app.todos.projects.schemas import (
    TodoProject as TodoProjectSchema,
    TodoProjectCreate,
    TodoProjectUpdate,
    TodoProjectOwner as TodoProjectOwnerSchema,
)
from src.app.auth.models import User
from src.app.auth.enums.actions import Actions
from src.app.auth.permission_helpers import get_categories_permissions
from src.app.auth.jwt_dependencies import get_current_active_user
from src.services.todo_access_service import can_user_access_project, is_general_project, user_is_project_owner
from src.app.todos.projects.service import (
    list_user_projects_schemas,
    get_owner_email,
    create_project,
    build_todo_project_schema,
)
from src.app.todos.collaborators.service import get_collaborator_emails

router = APIRouter()


@router.get("", response_model=list[TodoProjectSchema])
async def list_todo_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """List all todo projects the user owns or collaborates on."""
    return await list_user_projects_schemas(db, UUID(str(current_user.id)))


@router.post("", response_model=TodoProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_todo_project(
    project: TodoProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.CREATE))
):
    """Create a new todo project."""
    db_project = await create_project(db, name=project.name, owner_id=UUID(str(current_user.id)))
    return await build_todo_project_schema(db, db_project)


@router.get("/{todo_project_id}", response_model=TodoProjectSchema)
async def get_todo_project(
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.READ))
):
    """Get a specific todo project if the user has access."""
    has_access = await can_user_access_project(
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

    # Build response via service helpers
    emails = await get_collaborator_emails(db, todo_project_id)
    owner_email = await get_owner_email(db, todo_project.owner_id)

    return TodoProjectSchema(
        id=int(todo_project.id),
        name=str(todo_project.name),
        created_at=todo_project.created_at,
        updated_at=todo_project.updated_at,
        is_general=bool(todo_project.is_general),
        collaborators=emails,
        owner=TodoProjectOwnerSchema(
            id=UUID(str(todo_project.owner_id)),
            email=str(owner_email or "")
        )
    )


@router.put("/{todo_project_id}", response_model=TodoProjectSchema)
async def update_todo_project(
    todo_project_update: TodoProjectUpdate,
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.UPDATE))
):
    """Update a todo project if the user has access and it's not a General project."""
    has_access = await can_user_access_project(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    # Check if General project
    if await is_general_project(db, todo_project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The General project cannot be modified or deleted"
        )

    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    for key, value in todo_project_update.model_dump(exclude_unset=True).items():
        setattr(todo_project, key, value)

    todo_project.updated_at = datetime.now()
    await db.commit()
    await db.refresh(todo_project)

    emails = await get_collaborator_emails(db, todo_project_id)
    owner_email = await get_owner_email(db, todo_project.owner_id)

    return TodoProjectSchema(
        id=int(todo_project.id),
        name=str(todo_project.name),
        created_at=todo_project.created_at,
        updated_at=todo_project.updated_at,
        is_general=bool(todo_project.is_general),
        collaborators=emails,
        owner=TodoProjectOwnerSchema(
            id=UUID(str(todo_project.owner_id)),
            email=str(owner_email or "")
        )
    )


@router.delete("/{todo_project_id}", status_code=204)
async def delete_todo_project(
    todo_project_id: Annotated[int, Path(...)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_categories_permissions(Actions.DELETE))
):
    """Delete a todo project if the user is the owner and it's not a General project."""
    is_owner = await user_is_project_owner(
        db, todo_project_id, UUID(str(current_user.id))
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action"
        )

    if await is_general_project(db, todo_project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The General project cannot be modified or deleted"
        )

    todo_project = await db.get(TodoProjectModel, todo_project_id)
    if not todo_project:
        raise HTTPException(status_code=404, detail="Todo project not found")

    await db.delete(todo_project)
    await db.commit()
