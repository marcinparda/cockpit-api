from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.todos.projects.models import TodoProject as TodoProjectModel
from src.services.todos.collaborators.models import TodoProjectCollaborator
from src.services.users.models import User
from datetime import datetime


async def list_projects_owned_by(db: AsyncSession, owner_id: UUID) -> List[TodoProjectModel]:
    res = await db.execute(
        select(TodoProjectModel).where(TodoProjectModel.owner_id == owner_id)
    )
    return list(res.scalars().all())


async def list_projects_collaborating_by(db: AsyncSession, user_id: UUID) -> List[TodoProjectModel]:
    res = await db.execute(
        select(TodoProjectModel)
        .join(TodoProjectCollaborator)
        .where(TodoProjectCollaborator.user_id == user_id)
    )
    return list(res.scalars().all())


async def get_owner_email(db: AsyncSession, owner_id: UUID) -> str:
    res = await db.execute(select(User.email).where(User.id == owner_id))
    return res.scalar_one()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalars().first()


async def create_project(db: AsyncSession, *, name: str, owner_id: UUID) -> TodoProjectModel:
    now = datetime.now()
    stmt = (
        insert(TodoProjectModel)
        .values(name=name, owner_id=owner_id, created_at=now, updated_at=now)
        .returning(TodoProjectModel)
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.scalar_one()
