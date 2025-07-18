"""User management endpoints for admin operations."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.user import (
    UserCreate, UserUpdate, UserWithRole, UserWithPermissions,
    UserPermissionAssign, UserPermissionRevoke, PasswordResetRequest,
    PasswordResetResponse
)
from src.schemas.permission import Permission as PermissionSchema
from src.services.user_service import (
    get_all_users, create_user, get_user_by_id, update_user, delete_user,
    assign_user_role, assign_user_permissions, revoke_user_permission,
    reset_user_password, get_user_with_role, get_user_with_permissions,
    get_user_permissions
)
from src.auth.dependencies import require_admin_role
from src.models.user import User

router = APIRouter()


@router.get("/", response_model=List[UserWithRole])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of users to return"),
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[UserWithRole]:
    """
    List all users with their roles (admin only).

    **Parameters:**
    - **skip**: Number of users to skip for pagination (default: 0)
    - **limit**: Maximum number of users to return (default: 100, max: 1000)

    **Returns:**
    - List of users with role information

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    """
    users = await get_all_users(db, skip=skip, limit=limit)
    return [UserWithRole.model_validate(user) for user in users]


@router.post("/", response_model=UserWithRole, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserWithRole:
    """
    Create a new user account (admin only).

    **Parameters:**
    - **email**: User's email address (must be unique)
    - **role_id**: Role to assign to the user
    - **password**: Optional password (generated if not provided)

    **Password Requirements (if provided):**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    **Returns:**
    - Created user with role information
    - **Note**: If password was generated, it should be communicated securely to the user

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **400 Bad Request**: Email already exists or invalid data
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: Role not found
    """
    user = await create_user(
        db=db,
        email=user_data.email,
        role_id=user_data.role_id,
        created_by_id=UUID(str(admin_user.id)),
        temporary_password=user_data.password
    )
    return UserWithRole.model_validate(user)


@router.get("/{user_id}", response_model=UserWithPermissions)
async def get_user_details(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserWithPermissions:
    """
    Get detailed user information including permissions (admin only).

    **Parameters:**
    - **user_id**: UUID of the user to retrieve

    **Returns:**
    - User details with role and permissions

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User not found
    """
    user = await get_user_with_permissions(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserWithPermissions.model_validate(user)


@router.put("/{user_id}", response_model=UserWithRole)
async def update_user_info(
    user_id: UUID,
    user_data: UserUpdate,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserWithRole:
    """
    Update user information (admin only).

    **Parameters:**
    - **user_id**: UUID of the user to update
    - **email**: New email address (optional)
    - **is_active**: New active status (optional)
    - **role_id**: New role ID (optional)

    **Returns:**
    - Updated user with role information

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **400 Bad Request**: Email already exists or invalid data
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User or role not found
    """
    user = await update_user(
        db=db,
        user_id=user_id,
        email=user_data.email,
        is_active=user_data.is_active,
        role_id=user_data.role_id
    )
    return UserWithRole.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete user account (admin only).

    **Parameters:**
    - **user_id**: UUID of the user to delete

    **Note:**
    - This permanently deletes the user and all associated permissions
    - Cannot be undone

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User not found
    """
    await delete_user(db, user_id)


@router.put("/{user_id}/role", response_model=UserWithRole)
async def change_user_role(
    user_id: UUID,
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> UserWithRole:
    """
    Change user's role (admin only).

    **Parameters:**
    - **user_id**: UUID of the user
    - **role_id**: UUID of the new role to assign

    **Returns:**
    - Updated user with new role information

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User or role not found
    """
    user = await assign_user_role(db, user_id, role_id)
    return UserWithRole.model_validate(user)


@router.post("/{user_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permissions_to_user(
    user_id: UUID,
    permission_data: UserPermissionAssign,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Assign permissions to user (admin only).

    **Parameters:**
    - **user_id**: UUID of the user
    - **permission_ids**: List of permission UUIDs to assign

    **Returns:**
    - Success message with count of assigned permissions

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **400 Bad Request**: One or more permissions already assigned
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User or permission not found
    """
    assignments = await assign_user_permissions(
        db, user_id, permission_data.permission_ids
    )
    return {
        "message": f"Successfully assigned {len(assignments)} permissions to user",
        "assigned_permissions": len(assignments)
    }


@router.delete("/{user_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission_from_user(
    user_id: UUID,
    permission_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Revoke specific permission from user (admin only).

    **Parameters:**
    - **user_id**: UUID of the user
    - **permission_id**: UUID of the permission to revoke

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: Permission assignment not found
    """
    await revoke_user_permission(db, user_id, permission_id)


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password_endpoint(
    user_id: UUID,
    reset_data: Optional[PasswordResetRequest] = None,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> PasswordResetResponse:
    """
    Reset user's password (admin only).

    **Parameters:**
    - **user_id**: UUID of the user
    - **new_password**: Optional new password (generated if not provided)

    **Password Requirements (if provided):**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    **Returns:**
    - New password (must be communicated securely to user)
    - Success message

    **Security Notes:**
    - User will be forced to change password on next login
    - Generated passwords are cryptographically secure
    - Communicate new password to user through secure channel

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **400 Bad Request**: Password validation failed
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User not found
    """
    new_password = await reset_user_password(
        db,
        user_id,
        reset_data.new_password if reset_data else None
    )
    return PasswordResetResponse(
        message="Password reset successfully",
        new_password=new_password
    )


@router.get("/{user_id}/permissions", response_model=List[PermissionSchema])
async def get_user_permissions_endpoint(
    user_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[PermissionSchema]:
    """
    Get all permissions assigned to a user (admin only).

    **Parameters:**
    - **user_id**: UUID of the user

    **Returns:**
    - List of permissions assigned to the user

    **Requires:**
    - Admin role
    - Valid JWT token

    **Errors:**
    - **401 Unauthorized**: Invalid or missing JWT token
    - **403 Forbidden**: User is not admin
    - **404 Not Found**: User not found
    """
    # Verify user exists
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    permissions = await get_user_permissions(db, user_id)
    return [PermissionSchema.model_validate(permission) for permission in permissions]
