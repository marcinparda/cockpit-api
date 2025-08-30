"""User permission management endpoints."""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.authorization.user_permissions.service import get_user_permissions
from src.core.database import get_db
from src.services.authorization.permissions.models import Permission
from src.services.authentication.dependencies import get_current_user
from src.services.users.models import User


router = APIRouter()


@router.get("/me", response_model=List[Permission])
async def get_current_user_permission(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's permissions."""
    return await get_user_permissions(db, UUID(str(current_user.id)))
