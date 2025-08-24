"""JWT dependencies with token extraction supporting both cookies and Bearer tokens."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.app.auth.jwt import verify_token
from src.app.users.service import get_user_with_role
from src.app.auth.models import User


# JWT Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_with_token(
    # Cookie-based authentication
    access_token: Optional[str] = Cookie(None),
    # Bearer token authentication (backward compatibility)
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> tuple[User, str]:
    """
    Get current authenticated user and their token from either cookie or Bearer token.

    Args:
        access_token: JWT token from httpOnly cookie
        authorization: Bearer token from Authorization header
        credentials: JWT token from HTTPBearer scheme (legacy)
        db: Database session

    Returns:
        Tuple of (User object, token string) for authenticated user

    Raises:
        HTTPException: If no valid authentication is provided or user not found
    """
    token = None

    # Try to get token from cookie first
    if access_token:
        token = access_token
    # Try direct authorization header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # Fall back to HTTPBearer credentials (legacy)
    elif credentials:
        token = credentials.credentials

    # No authentication provided
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide either cookie or Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify and decode JWT token with database validation
        payload = await verify_token(token, db)
        user_id_str = payload.get("sub")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(user_id_str)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = await get_user_with_role(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user, token


async def get_current_user(
    # Cookie-based authentication
    access_token: Optional[str] = Cookie(None),
    # Bearer token authentication (backward compatibility)
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from either cookie or Bearer token.

    This function supports both authentication methods:
    1. HTTP-only cookie (preferred for web browsers)
    2. Bearer token in Authorization header (for API clients)

    Args:
        access_token: JWT token from httpOnly cookie
        authorization: Bearer token from Authorization header
        credentials: JWT token from HTTPBearer scheme (legacy)
        db: Database session

    Returns:
        User object for authenticated user

    Raises:
        HTTPException: If no valid authentication is provided or user not found
    """
    token = None

    # Try to get token from cookie first
    if access_token:
        token = access_token
    # Try direct authorization header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # Fall back to HTTPBearer credentials (legacy)
    elif credentials:
        token = credentials.credentials

    # No authentication provided
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: provide either cookie or Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify and decode JWT token with database validation
        payload = await verify_token(token, db)
        user_id_str = payload.get("sub")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(user_id_str)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = await get_user_with_role(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (convenience dependency).

    Args:
        current_user: Current authenticated user

    Returns:
        User object for active authenticated user
    """
    return current_user
