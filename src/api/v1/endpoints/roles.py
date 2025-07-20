"""Role management endpoints for admin operations."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.user_role import UserRole as UserRoleSchema
from src.schemas.permission import Permission as PermissionSchema
from src.services.user_service import get_all_roles
from src.auth.dependencies import require_admin_role
from src.models.user import User

router = APIRouter()


@router.get("", response_model=List[UserRoleSchema], tags=["admin"])
async def list_all_roles(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[UserRoleSchema]:
    """List all available user roles (admin only)."""
    roles = await get_all_roles(db)
    return [UserRoleSchema.model_validate(role) for role in roles]


@router.get("/{role_id}/permissions", response_model=List[PermissionSchema], tags=["admin"])
async def get_role_default_permissions(
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[PermissionSchema]:
    """Get default permissions for a specific role (admin only)."""
    # For now, return empty list as permissions are assigned individually
    # This could be extended to show recommended permissions per role
    return []
