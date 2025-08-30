from uuid import UUID
from typing import Annotated
from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.authentication.dependencies import get_current_user
from src.services.authorization.permissions.dependencies import require_permission
from src.services.authorization.permissions.enums import Actions, Features
from src.services.users.models import User
from src.services.todos.items.service import can_user_access_item, get_item_by_id
from src.services.todos.items.models import TodoItem


async def can_access_item(
    item_id: Annotated[int, Path(...)],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TodoItem:
    """
    Dependency to require access to a todo item (via project ownership or collaboration).
    Raises 404 if the item does not exist, 403 if the current user has no access.
    Returns the TodoItem model instance when allowed.
    """
    item = await get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo item not found"
        )

    has_access = await can_user_access_item(
        db, item_id, UUID(str(current_user.id))
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this item is forbidden"
        )

    return item


def get_todo_items_permissions(action: Actions):
    """User-based todo items permissions dependency."""
    return require_permission(Features.TODO_ITEMS, action)
