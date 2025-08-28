"""User management endpoints for admin operations."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.authentication.dependencies import get_current_user
from src.core.database import get_db
from .schemas import (
    UserCreate, UserUpdate, UserWithRole,
    UserPermissionAssign,
    UserPermissionAssignResponse, SimpleUserResponse
)
from src.services.authorization.permissions.models import Permission
from .service import (
    get_all_users, get_user_by_id, update_user, delete_user,
    assign_user_role, assign_user_permissions, revoke_user_permission, onboard_new_user
)
from src.services.authorization.permissions.service import get_user_permissions
from src.services.authorization.permissions.dependencies import require_admin_role
from src.services.users.models import User

router = APIRouter()


@router.get("", response_model=List[SimpleUserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of users to return"),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[SimpleUserResponse]:
    """List all users with their roles."""
    users = await get_all_users(db, skip=skip, limit=limit)
    return [SimpleUserResponse.model_validate(user, from_attributes=True) for user in users]


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Create a new user account (admin only)."""
    user = await onboard_new_user(
        db=db,
        email=user_data.email,
        role_id=user_data.role_id,
        created_by_id=UUID(str(admin_user.id)),
        temporary_password=user_data.password
    )
    return User.model_validate(user)


@router.get("/{user_id}", response_model=User)
async def get_user_details(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get detailed user information including permissions (admin only)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return User.model_validate(user)


@router.put("/{user_id}", response_model=User)
async def update_user_info(
    user_id: UUID,
    user_data: UserUpdate,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Update user information (admin only)."""
    user = await update_user(
        db=db,
        user_id=user_id,
        email=user_data.email,
        is_active=user_data.is_active,
        role_id=user_data.role_id
    )
    return User.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete user account (admin only)."""
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.put("/{user_id}/role", response_model=UserWithRole)
async def change_user_role(
    user_id: UUID,
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserWithRole:
    """Change user's role (admin only)."""
    user = await assign_user_role(db, user_id, role_id)
    return UserWithRole.model_validate(user)


@router.post("/{user_id}/permissions", response_model=UserPermissionAssignResponse, status_code=status.HTTP_201_CREATED)
async def assign_permissions_to_user(
    user_id: UUID,
    permission_data: UserPermissionAssign,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserPermissionAssignResponse:
    """Assign permissions to user (admin only)."""
    assignments = await assign_user_permissions(
        db, user_id, permission_data.permission_ids
    )
    return UserPermissionAssignResponse(
        message=f"Successfully assigned {len(assignments)} permissions to user",
        assigned_permissions=len(assignments)
    )


@router.delete("/{user_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission_from_user(
    user_id: UUID,
    permission_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Revoke specific permission from user (admin only)."""
    await revoke_user_permission(db, user_id, permission_id)


@router.get("/{user_id}/permissions", response_model=List[Permission])
async def get_user_permissions_endpoint(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[Permission]:
    """Get all permissions assigned to a user (admin only)."""
    # Verify user exists
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    permissions = await get_user_permissions(db, user_id)
    return [Permission.model_validate(permission) for permission in permissions]
