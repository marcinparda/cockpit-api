"""Password management endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.authentication.passwords.schemas import (
    PasswordChangeRequest, PasswordChangeResponse
)
from src.services.users.service import change_user_password
from src.services.authentication.shared.dependencies import get_current_user
from src.services.authentication.shared.exception_utils import password_change_exception_handler
from src.services.users.models import User


router = APIRouter()


@router.post("/change", response_model=PasswordChangeResponse)
@password_change_exception_handler
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PasswordChangeResponse:
    """Change current user's password."""
    success = await change_user_password(
        db=db,
        user_id=UUID(str(current_user.id)),
        current_password=password_request.current_password,
        new_password=password_request.new_password
    )

    if success:
        return PasswordChangeResponse(message="Password changed successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
