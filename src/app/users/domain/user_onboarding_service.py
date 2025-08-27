"""
User onboarding domain service.

This service handles cross-aggregate business rules for user creation,
specifically coordinating between User and TodoProject aggregates to ensure
new users get their required General project.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.users import service as users_service
from src.app.todos.projects.service import create_project
from src.app.users.models import User


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
    general_project = await create_project(
        db,
        name="General",
        owner_id=UUID(str(new_user.id))
    )
    db.add(general_project)
    await db.commit()
    
    # Load role relationship for return
    await db.refresh(new_user, ["role"])
    
    return new_user