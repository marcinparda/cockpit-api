"""Authorization endpoints for permissions and roles management."""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.authentication.schemas import (
    Permission,
    UserRole,
)
from src.app.users.service import get_user_with_permissions, get_all_roles, get_user_with_role
from src.app.authentication.jwt_dependencies import get_current_active_user
from src.app.authorization.dependencies import require_admin_role
from src.app.users.models import User


router = APIRouter()


@router.get("/me/permissions", response_model=List[Permission])
async def get_current_user_permission(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permissions."""
    user = await get_user_with_permissions(db, UUID(str(current_user.id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [up.permission for up in user.permissions if up.permission]


@router.get("/me/roles", response_model=List[str])
async def get_current_user_roles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's roles as a list of role names (strings)."""
    user = await get_user_with_role(db, UUID(str(current_user.id)))
    if not user or not user.role:
        raise HTTPException(status_code=404, detail="User or role not found")
    return [user.role.name]


@router.get("/roles", response_model=List[UserRole], tags=["admin"])
async def list_all_roles(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[UserRole]:
    """List all available user roles (admin only)."""
    roles = await get_all_roles(db)
    return [UserRole.model_validate(role) for role in roles]


@router.get("/roles/{role_id}/permissions", response_model=List[Permission], tags=["admin"])
async def get_role_default_permissions(
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[Permission]:
    """Get default permissions for a specific role (admin only)."""
    # For now, return empty list as permissions are assigned individually
    # This could be extended to show recommended permissions per role
    return []
