from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.todos.projects.models import TodoProject as TodoProjectModel
from src.app.auth.models import User
from src.app.todos.projects import repository
from src.app.todos.projects.schemas import (
    TodoProject as TodoProjectSchema,
    TodoProjectOwner as TodoProjectOwnerSchema,
)
from src.app.todos.collaborators.service import get_collaborator_emails


async def get_owned_projects(db: AsyncSession, user_id: UUID) -> List[TodoProjectModel]:
    """Return projects where the user is the owner."""
    return await repository.list_projects_owned_by(db, user_id)


async def get_collab_projects(db: AsyncSession, user_id: UUID) -> List[TodoProjectModel]:
    """Return projects where the user is a collaborator."""
    return await repository.list_projects_collaborating_by(db, user_id)


async def get_owner_email(db: AsyncSession, owner_id: UUID) -> str:
    return await repository.get_owner_email(db, owner_id)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    return await repository.get_user_by_id(db, user_id)


async def create_project(
    db: AsyncSession, *, name: str, owner_id: UUID
) -> TodoProjectModel:
    """Create a TodoProject using Core insert and return the ORM row."""
    return await repository.create_project(db, name=name, owner_id=owner_id)


async def build_todo_project_schema(
    db: AsyncSession, project: TodoProjectModel
) -> TodoProjectSchema:
    emails = await get_collaborator_emails(db, project.id)
    owner_email = await get_owner_email(db, project.owner_id)
    return TodoProjectSchema(
        id=int(project.id),
        name=str(project.name),
        created_at=project.created_at,
        updated_at=project.updated_at,
        is_general=project.is_general,
        collaborators=emails,
        owner=TodoProjectOwnerSchema(
            id=project.owner_id,
            email=owner_email,
        ),
    )


async def list_user_projects_schemas(
    db: AsyncSession, user_id: UUID
) -> List[TodoProjectSchema]:
    """Return all projects for a user (owned or collaborating) as schema models."""
    owned_projects = await get_owned_projects(db, user_id)
    collab_projects = await get_collab_projects(db, user_id)

    # Deduplicate by id, keep first occurrence (owned has priority)
    projects_by_id: dict[int, TodoProjectModel] = {
        owned_project.id: owned_project for owned_project in owned_projects}

    for collab_project in collab_projects:
        if collab_project.id not in projects_by_id:
            projects_by_id[collab_project.id] = collab_project

    projects: List[TodoProjectSchema] = []
    for project in projects_by_id.values():
        projects.append(await build_todo_project_schema(db, project))
    return projects
