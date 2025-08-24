"""User service for user management operations."""

from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, delete
from fastapi import HTTPException, status
import secrets
import string

from src.app.auth.models import User
from src.app.auth.models import UserRole
from src.app.auth.models import UserPermission
from src.app.auth.models import Permission
from src.app.auth.password import hash_password, verify_password, validate_password_strength
from src.app.auth.enums.roles import Roles
from src.app.todos.projects.service import create_project


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_user_with_role(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user with role information.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User object with role loaded, None if not found
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_with_permissions(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user with role and permissions information.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User object with role and permissions loaded, None if not found
    """
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.permissions).selectinload(
                UserPermission.permission)
        )
        .where(User.id == user_id)
    )
    return result.scalars().first()


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
    setattr(user, 'password_hash', new_password_hash)
    setattr(user, 'password_changed', True)

    await db.commit()
    await db.refresh(user)

    return True


async def get_user_permissions(db: AsyncSession, user_id: UUID) -> Sequence[Permission]:
    """
    Get all permissions for a user.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        Sequence of Permission objects
    """
    # Get user with role
    user = await get_user_with_role(db, user_id)
    if not user or user.is_active is False:
        return []

    # Admin users have all permissions
    if user.role and user.role.name == Roles.ADMIN.value:
        result = await db.execute(select(Permission))
        return result.scalars().all()

    # Get user-specific permissions
    result = await db.execute(
        select(Permission)
        .join(UserPermission)
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()


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
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


async def create_user(
    db: AsyncSession,
    email: str,
    role_id: UUID,
    created_by_id: UUID,
    temporary_password: Optional[str] = None
) -> User:
    """
    Create a new user (admin only).

    Args:
        db: Database session
        email: User's email address
        role_id: Role to assign to user
        created_by_id: ID of admin creating the user
        temporary_password: Optional password (generated if not provided)

    Returns:
        Created User object

    Raises:
        HTTPException: If email already exists or role not found
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Verify role exists
    role_result = await db.execute(
        select(UserRole).where(UserRole.id == role_id)
    )
    role = role_result.scalars().first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Generate password if not provided
    if not temporary_password:
        temporary_password = generate_temporary_password()

    # Validate password strength
    is_valid, errors = validate_password_strength(temporary_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(errors)}"
        )

    # Hash password
    password_hash = hash_password(temporary_password)

    # Create user
    new_user = User(
        email=email,
        password_hash=password_hash,
        role_id=role_id,
        created_by=created_by_id,
        is_active=True,
        password_changed=False
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    general_project = await create_project(
        db,
        name="General",
        owner_id=UUID(str(new_user.id))
    )
    db.add(general_project)
    await db.commit()

    # Load role relationship
    await db.refresh(new_user, ["role"])

    return new_user


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    role_id: Optional[UUID] = None
) -> User:
    """
    Update user information (admin only).

    Args:
        db: Database session
        user_id: User ID to update
        email: New email address (optional)
        is_active: New active status (optional)
        role_id: New role ID (optional)

    Returns:
        Updated User object

    Raises:
        HTTPException: If user not found or email already exists
    """
    # Get user
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check email uniqueness if provided
    if email and email != user.email:
        existing_user = await get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        setattr(user, 'email', email)

    # Update is_active if provided
    if is_active is not None:
        setattr(user, 'is_active', is_active)

    # Update role if provided
    if role_id:
        role_result = await db.execute(
            select(UserRole).where(UserRole.id == role_id)
        )
        role = role_result.scalars().first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        setattr(user, 'role_id', role_id)

    await db.commit()
    await db.refresh(user)

    # Load role relationship
    await db.refresh(user, ["role"])

    return user


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
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete user (cascade will handle permissions)
    await db.delete(user)
    await db.commit()

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
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify all permissions exist
    permissions_result = await db.execute(
        select(Permission).where(Permission.id.in_(permission_ids))
    )
    permissions = permissions_result.scalars().all()

    if len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more permissions not found"
        )

    # Check for existing assignments
    existing_result = await db.execute(
        select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id.in_(permission_ids)
            )
        )
    )
    existing_permissions = existing_result.scalars().all()

    if existing_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permissions already assigned to user"
        )

    # Create new assignments
    new_assignments = []
    for permission_id in permission_ids:
        user_permission = UserPermission(
            user_id=user_id,
            permission_id=permission_id
        )
        db.add(user_permission)
        new_assignments.append(user_permission)

    await db.commit()

    # Refresh all assignments
    for assignment in new_assignments:
        await db.refresh(assignment)

    return new_assignments


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
    result = await db.execute(
        delete(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id
            )
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission assignment not found"
        )

    await db.commit()
    return True


async def reset_user_password(
    db: AsyncSession,
    user_id: UUID,
    new_password: Optional[str] = None
) -> str:
    """
    Reset user password (admin only).

    Args:
        db: Database session
        user_id: User ID
        new_password: New password (generated if not provided)

    Returns:
        The new password (for admin to communicate to user)

    Raises:
        HTTPException: If user not found or password validation fails
    """
    # Get user
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate password if not provided
    if not new_password:
        new_password = generate_temporary_password()

    # Validate password strength
    is_valid, errors = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(errors)}"
        )

    # Hash new password
    password_hash = hash_password(new_password)

    # Update user
    setattr(user, 'password_hash', password_hash)
    # Force password change on next login
    setattr(user, 'password_changed', False)

    await db.commit()
    await db.refresh(user)

    return new_password


async def get_all_roles(db: AsyncSession) -> Sequence[UserRole]:
    """
    Get all available roles (admin only).

    Args:
        db: Database session

    Returns:
        Sequence of UserRole objects
    """
    result = await db.execute(
        select(UserRole).order_by(UserRole.name)
    )
    return result.scalars().all()
