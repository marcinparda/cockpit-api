"""Role management endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from .schemas import UserRole
from src.services.authorization.roles.service import get_all_roles, get_user_roles_by_id
from src.services.authentication.dependencies import get_current_user
from src.services.authorization.permissions.dependencies import require_admin_role
from src.services.users.models import User
from uuid import UUID


router = APIRouter()


@router.get("/me", response_model=List[UserRole])
async def get_current_user_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's roles as a list of role names (strings)."""
    user_roles = await get_user_roles_by_id(db, UUID(str(current_user.id)))
    return [UserRole.model_validate(role) for role in user_roles.roles if role]


@router.get("/", response_model=List[UserRole])
async def list_all_roles(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[UserRole]:
    """List all available user roles (admin only)."""
    all_roles = await get_all_roles(db)
    return [UserRole.model_validate(role) for role in all_roles]
