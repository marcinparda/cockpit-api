"""Permission system core endpoints."""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from .schemas import Permission
from src.services.authorization.shared.dependencies import require_admin_role
from src.services.users.models import User


router = APIRouter()


@router.get("/{role_id}", response_model=List[Permission])
async def get_role_default_permissions(
    role_id: UUID,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[Permission]:
    """Get default permissions for a specific role (admin only)."""
    # For now, return empty list as permissions are assigned individually
    # This could be extended to show recommended permissions per role
    return []
