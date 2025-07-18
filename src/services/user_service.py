"""User service for user management operations."""

from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from src.models.user import User
from src.models.user_role import UserRole
from src.models.user_permission import UserPermission
from src.models.permission import Permission
from src.auth.password import hash_password, verify_password, validate_password_strength


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
            selectinload(User.permissions).selectinload(UserPermission.permission)
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


async def check_user_permission(
    db: AsyncSession, 
    user_id: UUID, 
    feature: str, 
    action: str
) -> bool:
    """
    Check if user has specific permission.
    
    Args:
        db: Database session
        user_id: User's UUID
        feature: Feature name
        action: Action name
        
    Returns:
        True if user has permission, False otherwise
    """
    # Get user with permissions
    user = await get_user_with_permissions(db, user_id)
    if not user:
        return False
    
    # Check if user has the specific permission
    for user_permission in user.permissions:
        permission = user_permission.permission
        if permission.feature_id == feature and permission.action_id == action:
            return True
    
    return False


async def get_user_permissions(db: AsyncSession, user_id: UUID) -> Sequence[Permission]:
    """
    Get all permissions for a user.
    
    Args:
        db: Database session
        user_id: User's UUID
        
    Returns:
        Sequence of Permission objects
    """
    result = await db.execute(
        select(Permission)
        .join(UserPermission)
        .where(UserPermission.user_id == user_id)
    )
    return result.scalars().all()
