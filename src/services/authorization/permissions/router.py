"""Permission system core endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.authorization.permissions.schemas import PermissionSchema
from src.services.authorization.permissions.dependencies import require_admin_role
from src.services.authorization.permissions import service as permission_service
from src.services.users.models import User


router = APIRouter()


@router.get("", response_model=List[PermissionSchema])
async def get_all_permissions(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
) -> List[PermissionSchema]:
    """Get all permissions (admin only)."""
    return await permission_service.get_all_permissions(db)
