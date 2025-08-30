"""User service for user management operations."""

from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import secrets
import string

from src.services.users.models import User
from src.services.users import repository
from src.services.authorization.user_permissions.models import UserPermission
from src.services.authentication.passwords.service import hash_password, verify_password, validate_password_strength
from src.services.users import service as users_service
from src.services.todos.projects import repository as projects_repository


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    """Get user by user ID."""
    user = await repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    return await repository.get_user_by_email(db, email)


async def change_user_password(
    db: AsyncSession,
    user_id: UUID,
    current_password: str,
    new_password: str
) -> bool:
    """
    Change user's password after validating current password.

    Args:
        db: Database session
        user_id: User's UUID
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        True if password changed successfully

    Raises:
        HTTPException: If validation fails
    """
    # Get user
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(current_password, str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, errors = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(errors)}"
        )

    # Hash new password
    new_password_hash = hash_password(new_password)

    # Update user
    user.password_hash = new_password_hash
    user.password_changed = True
    await repository.update_user(db, user)

    return True


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password.

    Args:
        length: Password length (default: 12)

    Returns:
        Randomly generated password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> Sequence[User]:
    """
    Get all users with role information (admin only).

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Sequence of User objects with roles loaded
    """
    return await repository.get_all_users(db, skip, limit)


async def create_user(
    db: AsyncSession,
    email: str,
    role_id: UUID,
    created_by_id: UUID,
    temporary_password: Optional[str] = None
) -> User:
    """Create a new user (admin only)."""
    existing_user = await repository.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    role = await repository.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if not temporary_password:
        temporary_password = generate_temporary_password()

    is_valid, errors = validate_password_strength(temporary_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(errors)}"
        )

    password_hash = hash_password(temporary_password)

    new_user = User(
        email=email,
        password_hash=password_hash,
        role_id=role_id,
        created_by=created_by_id,
        is_active=True,
        password_changed=False
    )

    return await repository.save_user(db, new_user)


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    role_id: Optional[UUID] = None
) -> User:
    """Update user information (admin only)."""
    user = await repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if email and email != user.email:
        existing_user = await repository.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    if role_id:
        role = await repository.get_role_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

    if email is not None:
        user.email = email
    if is_active is not None:
        user.is_active = is_active
    if role_id is not None:
        user.role_id = role_id

    return await repository.update_user(db, user)


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """
    Delete user (admin only).

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        True if user was deleted

    Raises:
        HTTPException: If user not found
    """
    # Get user
    user = await repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete user (cascade will handle permissions)
    await repository.delete_user_record(db, user)

    return True


async def assign_user_role(
    db: AsyncSession,
    user_id: UUID,
    role_id: UUID
) -> User:
    """
    Assign role to user (admin only).

    Args:
        db: Database session
        user_id: User ID
        role_id: Role ID to assign

    Returns:
        Updated User object

    Raises:
        HTTPException: If user or role not found
    """
    return await update_user(db, user_id, role_id=role_id)


async def assign_user_permissions(
    db: AsyncSession,
    user_id: UUID,
    permission_ids: List[UUID]
) -> List[UserPermission]:
    """
    Assign permissions to user (admin only).

    Args:
        db: Database session
        user_id: User ID
        permission_ids: List of permission IDs to assign

    Returns:
        List of created UserPermission objects

    Raises:
        HTTPException: If user not found or permission already assigned
    """
    # Verify user exists
    user = await repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify all permissions exist
    permissions = await repository.get_permissions_by_ids(db, permission_ids)

    if len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more permissions not found"
        )

    # Check for existing assignments
    existing_permissions = await repository.get_existing_user_permissions(
        db, user_id, permission_ids
    )

    if existing_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permissions already assigned to user"
        )

    # Create new assignments
    new_assignments = [
        UserPermission(user_id=user_id, permission_id=permission_id)
        for permission_id in permission_ids
    ]

    return await repository.save_user_permissions(db, new_assignments)


async def revoke_user_permission(
    db: AsyncSession,
    user_id: UUID,
    permission_id: UUID
) -> bool:
    """
    Revoke specific permission from user (admin only).

    Args:
        db: Database session
        user_id: User ID
        permission_id: Permission ID to revoke

    Returns:
        True if permission was revoked

    Raises:
        HTTPException: If permission assignment not found
    """
    # Delete the permission assignment
    deleted_count = await repository.delete_user_permission(db, user_id, permission_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission assignment not found"
        )

    return True


async def onboard_new_user(
    db: AsyncSession,
    email: str,
    role_id: UUID,
    created_by_id: UUID,
    temporary_password: Optional[str] = None
) -> User:
    """
    Onboard a new user by creating their account and setting up their workspace.

    This domain service handles the cross-aggregate business rule that every new user
    must have a General project created for their todo management.

    Args:
        db: Database session
        email: User's email address
        role_id: Role to assign to user
        created_by_id: ID of admin creating the user
        temporary_password: Optional password (generated if not provided)

    Returns:
        Created User object with role relationship loaded

    Raises:
        HTTPException: If email already exists, role not found, or validation fails
    """
    # Create the user account
    new_user = await users_service.create_user(
        db=db,
        email=email,
        role_id=role_id,
        created_by_id=created_by_id,
        temporary_password=temporary_password
    )

    # Create the user's General project (cross-aggregate business rule)
    await projects_repository.create_project(
        db,
        name="General",
        owner_id=UUID(str(new_user.id))
    )

    # Load role relationship for return
    await repository.refresh_user_with_role(db, new_user)

    return new_user
