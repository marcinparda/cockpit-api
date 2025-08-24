from __future__ import annotations

from typing import List, Sequence, Optional
from uuid import UUID

from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.todos.collaborators.models import TodoProjectCollaborator
from src.app.todos.projects.models import TodoProject
from src.app.auth.models import User


async def list_project_collaborators(db: AsyncSession, project_id: int) -> List[TodoProjectCollaborator]:
    res = await db.execute(
        select(TodoProjectCollaborator).where(
            TodoProjectCollaborator.project_id == project_id
        )
    )
    return list(res.scalars().all())


async def list_project_collaborator_user_ids(db: AsyncSession, project_id: int) -> List[UUID]:
    res = await db.execute(
        select(TodoProjectCollaborator.user_id).where(
            TodoProjectCollaborator.project_id == project_id
        )
    )
    return list(res.scalars().all())


async def get_users_by_ids(db: AsyncSession, user_ids: Sequence[UUID]) -> List[User]:
    if not user_ids:
        return []
    res = await db.execute(select(User).where(User.id.in_(user_ids)))
    return list(res.scalars().all())


async def get_existing_collaborator_user_ids(
    db: AsyncSession, project_id: int, user_ids: Sequence[UUID]
) -> List[UUID]:
    if not user_ids:
        return []
    res = await db.execute(
        select(TodoProjectCollaborator.user_id).where(
            and_(
                TodoProjectCollaborator.project_id == project_id,
                TodoProjectCollaborator.user_id.in_(user_ids),
            )
        )
    )
    return list(res.scalars().all())


async def get_collaborator_emails(db: AsyncSession, project_id: int) -> List[str]:
    collaborators_emails = await db.execute(
        select(User.email)
        .join(TodoProjectCollaborator, User.id == TodoProjectCollaborator.user_id)
        .where(TodoProjectCollaborator.project_id == project_id)
    )
    return [email for email in collaborators_emails.scalars().all()]


async def create_collaborators(db: AsyncSession, project_id: int, user_ids: Sequence[UUID]) -> None:
    values = [{"project_id": project_id, "user_id": uid} for uid in user_ids]
    await db.execute(insert(TodoProjectCollaborator), values)
    await db.commit()


async def get_collaborator_by_project_and_user(
    db: AsyncSession, project_id: int, user_id: UUID
) -> Optional[TodoProjectCollaborator]:
    res = await db.execute(
        select(TodoProjectCollaborator).where(
            and_(
                TodoProjectCollaborator.project_id == project_id,
                TodoProjectCollaborator.user_id == user_id,
            )
        )
    )
    return res.scalars().first()
