from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, asc
from uuid import UUID
from typing import Annotated

from src.core.database import get_db
from src.models.todo_item import TodoItem
from src.models.todo_project import TodoProject
from src.models.user import User
from src.schemas.todo_item import (
    TodoItem as TodoItemSchema,
    TodoItemCreate,
    TodoItemUpdate,
)
from src.auth.enums.actions import Actions
from src.auth.permission_helpers import get_todo_items_permissions
from src.auth.jwt_dependencies import get_current_active_user
from src.api.v1.deps import (
    require_project_access,
    require_item_access
)

router = APIRouter()


@router.get("", response_model=List[TodoItemSchema])
async def get_todo_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    sort_by: str = Query(
        "name", description="Field to sort by: id, name, created_at, updated_at, is_closed, completed_at"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """Retrieve todo items from projects the user has access to."""
    from src.services.todo_access_service import get_accessible_project_ids

    # Get all project IDs the user has access to
    project_ids = await get_accessible_project_ids(db, UUID(str(current_user.id)))

    allowed_sort_fields = {"id", "name", "created_at",
                           "updated_at", "is_closed", "completed_at"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by field: {sort_by}")

    order_func = desc if order.lower() == "desc" else asc
    sort_column = getattr(TodoItem, sort_by)

    # Filter items by accessible projects
    result = await db.execute(
        select(TodoItem)
        .options(selectinload(TodoItem.project))
        .where(TodoItem.project_id.in_(project_ids))
        .order_by(order_func(sort_column))
        .offset(skip)
        .limit(limit)
    )

    items = result.scalars().all()

    # Manually convert items to dict to avoid async relationship issues
    items_list = []
    for item in items:
        # Convert project to dict with string owner_id
        project_dict = None
        if item.project:
            project_dict = {
                "id": item.project.id,
                "name": item.project.name,
                "created_at": item.project.created_at,
                "updated_at": item.project.updated_at,
                "owner_id": str(item.project.owner_id),
                "is_general": item.project.is_general
            }

        # Convert item to dict
        item_dict = {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "is_closed": item.is_closed,
            "shops": item.shops,
            "project_id": item.project_id,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "completed_at": item.completed_at,
            "project": project_dict
        }
        items_list.append(item_dict)

    return items_list


@router.post("", response_model=TodoItemSchema, status_code=status.HTTP_201_CREATED)
async def create_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: TodoItemCreate,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_todo_items_permissions(Actions.CREATE))
) -> Any:
    """Create new todo item in a project the user has access to."""
    # Check if project_id is provided
    if not item_in.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id is required"
        )

    # Check if user has access to the project
    from src.services.todo_access_service import user_can_access_project
    project_id = item_in.project_id
    has_access = await user_can_access_project(
        db, project_id, UUID(str(current_user.id))
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this project is forbidden"
        )

    # Get the project
    project = await db.get(TodoProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create the item
    now = datetime.utcnow()
    db_item = TodoItem(
        name=item_in.name,
        description=item_in.description,
        is_closed=False,
        shops=item_in.shops,
        project_id=project_id,
        created_at=now,
        updated_at=now
    )
    db.add(db_item)
    await db.commit()
    # Eagerly load the project relationship after creation
    await db.refresh(db_item, attribute_names=["project"])

    # Manually convert item to dict to avoid async relationship issues
    # Convert project to dict with string owner_id
    project_dict = None
    if db_item.project:
        project_dict = {
            "id": db_item.project.id,
            "name": db_item.project.name,
            "created_at": db_item.project.created_at,
            "updated_at": db_item.project.updated_at,
            "owner_id": str(db_item.project.owner_id),
            "is_general": db_item.project.is_general
        }

    # Convert item to dict
    item_dict = {
        "id": db_item.id,
        "name": db_item.name,
        "description": db_item.description,
        "is_closed": db_item.is_closed,
        "shops": db_item.shops,
        "project_id": db_item.project_id,
        "created_at": db_item.created_at,
        "updated_at": db_item.updated_at,
        "completed_at": db_item.completed_at,
        "project": project_dict
    }

    return item_dict


@router.get("/{item_id}", response_model=TodoItemSchema)
async def get_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: Annotated[int, Path(...)],
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_todo_items_permissions(Actions.READ))
) -> Any:
    """Get todo item by ID if the user has access to its project."""
    # First, get the item
    item = await db.get(TodoItem, item_id, options=[selectinload(TodoItem.project)])
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    # Check if user has access to the project
    from src.services.todo_access_service import user_can_access_project
    if item.project_id:
        has_access = await user_can_access_project(
            db, item.project_id, UUID(str(current_user.id))
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this item is forbidden"
            )

    # Manually convert item to dict to avoid async relationship issues
    # Convert project to dict with string owner_id
    project_dict = None
    if item.project:
        project_dict = {
            "id": item.project.id,
            "name": item.project.name,
            "created_at": item.project.created_at,
            "updated_at": item.project.updated_at,
            "owner_id": str(item.project.owner_id),
            "is_general": item.project.is_general
        }

    # Convert item to dict
    item_dict = {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "is_closed": item.is_closed,
        "shops": item.shops,
        "project_id": item.project_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "completed_at": item.completed_at,
        "project": project_dict
    }

    return item_dict


@router.put("/{item_id}", response_model=TodoItemSchema)
async def update_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: Annotated[int, Path(...)],
    item_in: TodoItemUpdate,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_todo_items_permissions(Actions.UPDATE))
) -> Any:
    """Update a todo item if the user has access to its project."""
    # First, get the item
    db_item = await db.get(TodoItem, item_id, options=[selectinload(TodoItem.project)])
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    # Check if user has access to the current project
    from src.services.todo_access_service import user_can_access_project
    if db_item.project_id:
        has_access = await user_can_access_project(
            db, db_item.project_id, UUID(str(current_user.id))
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this item is forbidden"
            )

    # If project_id is changing, check access to the new project
    update_data = item_in.dict(exclude_unset=True)
    if "project_id" in update_data:
        new_project_id = update_data["project_id"]
        if new_project_id is not None:
            # Check access to the new project
            has_access = await user_can_access_project(
                db, new_project_id, UUID(str(current_user.id))
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to the target project is forbidden"
                )

            # Verify project exists
            project = await db.get(TodoProject, new_project_id)
            if not project:
                raise HTTPException(
                    status_code=404, detail="Project not found")

            # Update the project
            db_item.project_id = new_project_id
        else:
            # Project ID cannot be null
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id cannot be null"
            )

        # Remove from update_data since we handled it
        del update_data["project_id"]

    # Update the other fields
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db_item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_item)

    # Manually convert item to dict to avoid async relationship issues
    # Convert project to dict with string owner_id
    project_dict = None
    if db_item.project:
        project_dict = {
            "id": db_item.project.id,
            "name": db_item.project.name,
            "created_at": db_item.project.created_at,
            "updated_at": db_item.project.updated_at,
            "owner_id": str(db_item.project.owner_id),
            "is_general": db_item.project.is_general
        }

    # Convert item to dict
    item_dict = {
        "id": db_item.id,
        "name": db_item.name,
        "description": db_item.description,
        "is_closed": db_item.is_closed,
        "shops": db_item.shops,
        "project_id": db_item.project_id,
        "created_at": db_item.created_at,
        "updated_at": db_item.updated_at,
        "completed_at": db_item.completed_at,
        "project": project_dict
    }

    return item_dict


@router.delete("/{item_id}", response_model=TodoItemSchema)
async def delete_todo_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: Annotated[int, Path(...)],
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(get_todo_items_permissions(Actions.DELETE))
) -> Any:
    """Delete a todo item if the user has access to its project."""
    # First, get the item
    db_item = await db.get(TodoItem, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    # Check if user has access to the project
    from src.services.todo_access_service import user_can_access_project
    if db_item.project_id:
        has_access = await user_can_access_project(
            db, db_item.project_id, UUID(str(current_user.id))
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this item is forbidden"
            )

    # Delete the item
    item_copy = TodoItemSchema.model_validate(db_item)
    await db.delete(db_item)
    await db.commit()
    return item_copy
