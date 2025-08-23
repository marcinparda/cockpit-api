"""Dependencies for Todo app collaboration feature."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.auth.jwt_dependencies import get_current_active_user
from src.models.user import User
from src.services.todo_access_service import (
    user_can_access_project,
    user_can_access_item,
    user_is_project_owner,
    is_general_project
)


def require_project_access(project_id: int):
    """
    Dependency to require project access (owner or collaborator).
    Raises HTTPException if user doesn't have access.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_access = await user_can_access_project(
            db, project_id, UUID(str(current_user.id))
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this project is forbidden"
            )

        return current_user

    return dependency


def require_project_ownership(project_id: int):
    """
    Dependency to require project ownership.
    Raises HTTPException if user is not the owner.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        is_owner = await user_is_project_owner(
            db, project_id, UUID(str(current_user.id))
        )

        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners can perform this action"
            )

        return current_user

    return dependency


def require_item_access(item_id: int):
    """
    Dependency to require access to a todo item.
    Raises HTTPException if user doesn't have access.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        has_access = await user_can_access_item(
            db, item_id, UUID(str(current_user.id))
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this item is forbidden"
            )

        return current_user

    return dependency


def prevent_general_project_modification(project_id: int):
    """
    Dependency to prevent modification of "General" projects.
    Raises HTTPException if the project is a General project.
    """
    async def dependency(
        db: AsyncSession = Depends(get_db)
    ):
        is_general = await is_general_project(db, project_id)

        if is_general:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The General project cannot be modified or deleted"
            )

        return True

    return dependency
