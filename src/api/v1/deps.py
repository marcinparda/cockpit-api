"""Dependencies for Todo app collaboration feature."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.auth.jwt_dependencies import get_current_active_user
from src.app.auth.models import User
from src.services.todo_access_service import (
    user_can_access_item,
    user_is_project_owner,
    is_general_project
)
from src.app.todos.items.models import TodoItem


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


def can_access_item(item_id: int):
    """
    Dependency to require access to a todo item (via project ownership or collaboration).
    Raises 404 if the item does not exist, 403 if the current user has no access.
    Returns the TodoItem model instance when allowed.
    """
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        # Ensure item exists
        item = await db.get(TodoItem, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo item not found"
            )

        has_access = await user_can_access_item(
            db, item_id, UUID(str(current_user.id))
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this item is forbidden"
            )

        return item

    return dependency
