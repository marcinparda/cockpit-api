from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from src.models.user import User
from src.auth.password import verify_password
from src.auth.jwt import create_access_token, create_token_response
from src.schemas.auth import LoginResponse, TokenResponse


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalars().first()
    
    if not user:
        return None
    
    # Check if user is active
    if not user.is_active:
        return None
    
    # Verify password
    if not verify_password(password, str(user.password_hash)):
        return None
    
    return user


async def create_user_token(user: User) -> TokenResponse:
    """
    Create JWT token for authenticated user.
    
    Args:
        user: Authenticated user object
        
    Returns:
        TokenResponse with access token and metadata
    """
    from uuid import UUID
    
    user_id = UUID(str(user.id))
    email = str(user.email)
    
    return create_token_response(user_id, email)


async def login_user(db: AsyncSession, email: str, password: str) -> LoginResponse:
    """
    Complete login flow for user authentication.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        LoginResponse with token and user details
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user = await authenticate_user(db, email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create token
    token_response = await create_user_token(user)
    
    # Create complete login response
    return LoginResponse(
        access_token=token_response.access_token,
        token_type=token_response.token_type,
        expires_in=token_response.expires_in,
        user_id=UUID(str(user.id)),
        email=str(user.email),
        is_active=bool(user.is_active),
        password_changed=bool(user.password_changed)
    )
